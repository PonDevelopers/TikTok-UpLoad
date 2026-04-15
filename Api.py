import os, json, time, random, logging, threading, requests
from datetime import datetime, timedelta
from pathlib import Path


# ─── Config ───────────────────────────────────────────────────────────────────

BASE_URL         = "http://localhost:8899"
API_KEY          = "lekhadz"
_HEADERS         = {"X-API-Key": API_KEY}

TIME_CONFIG   = "Time.json"
COOKIES_FILE  = "Cookies.txt"
CAPTION_FILE  = "Caption.txt"
HASHTAG_FILE  = "Hashtag.txt"
DATABASE_FILE = "Database.json"

TELEGRAM_TOKEN   = ""
TELEGRAM_CHAT_ID = ""

# ─── Globals ──────────────────────────────────────────────────────────────────

stop_event        = threading.Event()
_db_lock          = threading.Lock()
_music_ids        = []
_music_index      = 0
_music_index_lock = threading.Lock()
_pending_info     = {}

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("log.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def clog(label, msg):
    logging.info(f"[{label}] {msg}")


# ─── Telegram ─────────────────────────────────────────────────────────────────

def _tg_send(payload):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=payload,
            timeout=10,
        )
    except Exception:
        pass


def tg_html(msg):
    _tg_send({
        "chat_id":               TELEGRAM_CHAT_ID,
        "text":                  msg,
        "parse_mode":            "HTML",
        "disable_web_page_preview": "true",
    })


def fmt_label(label):
    import re
    return re.sub(
        r'@([\w.]+)',
        lambda m: f'<a href="https://tiktok.com/@{m.group(1)}">@{m.group(1)}</a>',
        label,
    )


# ─── Database ─────────────────────────────────────────────────────────────────

def db_load():
    if not os.path.exists(DATABASE_FILE):
        return {}
    with open(DATABASE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _db_save(data):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def db_record_upload(label, video_name, url, success):
    with _db_lock:
        data = db_load()
        if label not in data:
            data[label] = {"uploaded": [], "failed": []}
        entry = {
            "video": video_name,
            "url":   url,
            "time":  datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        key = "uploaded" if success else "failed"
        data[label][key].append(entry)
        _db_save(data)


def db_save_music_index(idx):
    with _db_lock:
        data = db_load()
        data["__music_index__"] = idx
        _db_save(data)


def db_load_music_index():
    return db_load().get("__music_index__", 0)


# ─── File loaders ─────────────────────────────────────────────────────────────

def load_captions():
    if not os.path.exists(CAPTION_FILE):
        return ["Great video"]
    with open(CAPTION_FILE, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines or ["Great video"]


def load_hashtags():
    if not os.path.exists(HASHTAG_FILE):
        return []
    with open(HASHTAG_FILE, encoding="utf-8") as f:
        content = f.read().strip()
    return [t.strip().lstrip("#") for t in content.replace("\n", ",").split(",") if t.strip()]


def load_time_config():
    with open(TIME_CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    slots = []
    for s in cfg.get("slots", []):
        start_str, end_str = s.split(" - ")
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        slots.append({"start": sh * 60 + sm, "end": eh * 60 + em, "label": s})
    return slots


def get_videos(folder):
    p = Path(folder)
    return sorted(p.glob("*.mp4"), key=lambda x: x.name) + sorted(p.glob("*.mov"), key=lambda x: x.name)


# ─── API calls ────────────────────────────────────────────────────────────────

def get_account_info(cookies):
    r = requests.post(
        f"{BASE_URL}/account",
        json={"cookies": cookies},
        headers=_HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise Exception(d.get("error", "unknown"))
    return d["data"]


def get_affiliate_info(cookies):
    r = requests.post(
        f"{BASE_URL}/affiliate",
        json={"cookies": cookies},
        headers=_HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise Exception(d.get("error", "unknown"))
    return d["data"]


def get_monetization_info(cookies):
    r = requests.post(
        f"{BASE_URL}/monetization",
        json={"cookies": cookies},
        headers=_HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise Exception(d.get("error", "unknown"))
    return d["data"]


def add_product(cookies, product_id):
    r = requests.post(
        f"{BASE_URL}/add_product",
        json={"cookies": cookies, "product_id": product_id},
        headers=_HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise Exception(d.get("error", "unknown"))
    return d["data"]


def _load_music_ids():
    global _music_ids, _music_index
    if not os.path.exists("Music.json"):
        return
    with open("Music.json", encoding="utf-8") as f:
        _music_ids = json.load(f)
    _music_index = db_load_music_index() % len(_music_ids) if _music_ids else 0
    logging.info(f"[Music] Resume from index {_music_index}/{len(_music_ids)}")


def load_music_for_slot():
    global _music_index
    if not _music_ids:
        return None
    for _ in range(len(_music_ids)):
        with _music_index_lock:
            idx          = _music_index
            _music_index = (_music_index + 1) % len(_music_ids)
        try:
            r    = requests.post(f"{BASE_URL}/music", json={"music_id": _music_ids[idx]}, headers=_HEADERS, timeout=15)
            data = r.json()
            if data.get("success"):
                music = data["data"]
                logging.info(f"[Music] {music['music_title']} - {music['music_author']}")
                db_save_music_index(_music_index)
                return music
        except Exception:
            pass
        logging.warning(f"[Music] id {_music_ids[idx]} failed, trying next")
    logging.error("[Music] Could not load any track")
    return None


def extract_product_id(filename):
    stem = Path(filename).stem
    return stem.split("_")[0] if "_" in stem else None


def get_product_info(video_path, use_product, cookies):
    if not use_product:
        return None, None
    try:
        pid = extract_product_id(video_path)
        if not pid:
            return None, None
        r = requests.post(
            f"{BASE_URL}/product",
            json={"cookies": cookies, "product_id": pid},
            headers=_HEADERS,
            timeout=15,
        )
        if r.ok:
            data  = r.json().get("data", {})
            title = data.get("title", "").strip()
            return pid, title or None
    except Exception:
        pass
    return None, None


def upload_video(cookies, video_path, caption, hashtags, music=None, product_id=None, product_title=None):
    data = {
        "cookies":             cookies,
        "caption":             caption,
        "hashtags":            ",".join(hashtags),
        "visibility":          0,
        "allow_comment":       1,
        "allow_content_reuse": 1,
    }
    if music:
        data["music"] = json.dumps(music)
    if product_id:
        data["product_id"]    = product_id
        data["product_title"] = product_title or ""
    with open(video_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/upload",
            data=data,
            files={"video": (os.path.basename(video_path), f, "video/mp4")},
            headers=_HEADERS,
            timeout=300,
        )
    r.raise_for_status()
    return r.json()


# ─── Slot helpers ─────────────────────────────────────────────────────────────

def _now_minutes():
    now = datetime.now()
    return now.hour * 60 + now.minute


def is_in_slot(slots):
    cur = _now_minutes()
    for s in slots:
        if s["start"] <= cur < s["end"]:
            return True, s
    return False, None


def next_slot_info(slots):
    cur = _now_minutes()
    for s in slots:
        if s["start"] > cur:
            return s, s["start"] - cur
    s = slots[0]
    return s, (24 * 60 - cur) + s["start"]


def wait_until_next_slot(slots, label):
    slot, wait_min = next_slot_info(slots)
    next_time = (datetime.now() + timedelta(minutes=wait_min)).strftime("%H:%M")
    clog(label, f"Outside slot. Waiting until {next_time} ({slot['label']})")
    for i in range(wait_min * 60):
        if stop_event.is_set():
            return
        if i % 60 == 0:
            if is_in_slot(load_time_config())[0]:
                return
        time.sleep(1)


def estimate_finish(videos_remaining, videos_per_hour, slots):
    if videos_per_hour <= 0 or videos_remaining <= 0 or not slots:
        return "N/A"
    minutes_needed = (videos_remaining / videos_per_hour) * 60
    now     = datetime.now()
    cur     = now.hour * 60 + now.minute
    sim_now = now
    remain  = minutes_needed
    for _ in range(365):
        for s in slots:
            avail_start = max(s["start"], cur)
            avail       = s["end"] - avail_start
            if avail <= 0:
                continue
            if remain <= avail:
                finish = sim_now + timedelta(minutes=(avail_start - cur) + remain)
                return finish.strftime("%d/%m/%Y %H:%M")
            remain -= avail
        sim_now += timedelta(minutes=24 * 60 - cur + slots[0]["start"])
        cur = slots[0]["start"]
    return "N/A"


# ─── Telegram listener ────────────────────────────────────────────────────────

def tg_listener(accounts_ref, slots_ref):
    offset = 0
    while not stop_event.is_set():
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35,
            )
            for u in r.json().get("result", []):
                offset  = u["update_id"] + 1
                msg     = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text    = msg.get("text", "").strip()

                if text == "/check":
                    _handle_check(accounts_ref, slots_ref)

                elif text == "/info":
                    _handle_info(accounts_ref, chat_id)

                elif text.startswith("/add_product "):
                    _handle_add_product(accounts_ref, text[len("/add_product "):].strip())

                elif chat_id in _pending_info and text.isdigit():
                    _handle_info_reply(chat_id, text)

        except Exception:
            time.sleep(5)


def _handle_add_product(accounts_ref, product_id):
    if not product_id:
        tg_html("Usage: <code>/add_product &lt;product_id&gt;</code>")
        return
    accounts = accounts_ref()
    if not accounts:
        tg_html("No accounts found.")
        return
    lines = [f"<b>Add product</b> <code>{product_id}</code>\n"]
    for acc in accounts:
        lbl = acc["label"]
        try:
            res = add_product(acc["cookies"], product_id)
            title  = res.get("title", "")
            price  = res.get("price", "")
            store  = res.get("store", "")
            stock  = res.get("stock", 0)
            comm   = res.get("commission", "")
            status = res.get("add_result", "")
            lines.append(
                f"<b>{fmt_label(lbl)}</b>\n"
                f"<blockquote>"
                f"Title:  {title}\n"
                f"Price:  {price}  |  Com: {comm}\n"
                f"Store:  {store}\n"
                f"Stock:  {stock:,}\n"
                f"Result: {status}"
                f"</blockquote>"
            )
        except Exception as e:
            lines.append(f"<b>{fmt_label(lbl)}</b>\n<blockquote>Error: {e}</blockquote>")
    tg_html("\n".join(lines))


def _handle_check(accounts_ref, slots_ref):
    slots          = slots_ref()
    in_s, cur_slot = is_in_slot(slots)
    if in_s:
        slot_line = f"Slot: {cur_slot['label']}"
    else:
        ns, wait_m = next_slot_info(slots)
        next_t     = (datetime.now() + timedelta(minutes=wait_m)).strftime("%H:%M")
        slot_line  = f"Next slot: {ns['label']} at {next_t}"

    db    = db_load()
    lines = [f"<b>STATUS</b> · {datetime.now().strftime('%H:%M %d/%m')}", slot_line, ""]

    for acc in accounts_ref():
        lbl      = acc["label"]
        vph      = acc.get("videos_per_hour", 1)
        acc_db   = db.get(lbl, {})
        done     = len(acc_db.get("uploaded", []))
        fail     = len(acc_db.get("failed", []))
        done_set = (
            {e["video"] for e in acc_db.get("uploaded", [])} |
            {e["video"] for e in acc_db.get("failed", [])}
        )
        left = len([v for v in get_videos(acc["folder"]) if v.name not in done_set])
        est  = estimate_finish(left, vph, slots)
        lines.append(
            f"<b>{fmt_label(lbl)}</b>\n"
            f"<blockquote>Done:    {done}\n"
            f"Failed:  {fail}\n"
            f"Left:    {left}\n"
            f"Speed:   {vph}/h\n"
            f"ETA:     {est}</blockquote>"
        )
    tg_html("\n".join(lines))


def _handle_info(accounts_ref, chat_id):
    accounts = accounts_ref()
    if not accounts:
        tg_html("No accounts found.")
        return
    _pending_info[chat_id] = accounts
    lines = ["<b>Select account:</b>"]
    for i, acc in enumerate(accounts, 1):
        lines.append(f"{i}. {acc['label']}")
    lines.append("\nReply with number, e.g. <code>1</code>")
    tg_html("\n".join(lines))


def _handle_info_reply(chat_id, text):
    accounts = _pending_info.pop(chat_id)
    idx      = int(text) - 1
    if not (0 <= idx < len(accounts)):
        tg_html(f"Invalid number (1-{len(accounts)})")
        return
    acc  = accounts[idx]
    try:
        info = get_account_info(acc["cookies"])
        acc["info"] = info
    except Exception:
        info = acc.get("info", {})
    lbl    = acc["label"]
    avatar = info.get("avatar", "")
    sig    = info.get("signature", "").strip()

    verified = "  |  Verified" if info.get("verified") else ""
    private  = "  |  Private"  if info.get("private")  else ""

    try:
        aff = get_affiliate_info(acc["cookies"])
        td  = aff.get("today", {})
        w7  = aff.get("last_7_days", {})
        aff_block = (
            f'\n\n<b>Affiliate</b>\n'
            f'<blockquote>'
            f'Today    GMV: {td.get("gmv","0")}  |  Sold: {td.get("items_sold","0")}  |  Com: {td.get("commission","0")}\n'
            f'7 Days   GMV: {w7.get("gmv","0")}  |  Sold: {w7.get("items_sold","0")}  |  Com: {w7.get("commission","0")}'
            f'</blockquote>'
        )
    except Exception:
        aff_block = ""

    try:
        m10n      = get_monetization_info(acc["cookies"])
        balance   = m10n.get("wallet_balance", "N/A")
        total_7d  = m10n.get("seven_d_income", "N/A")
        programs  = m10n.get("programs", [])
        prog_lines = []
        for p in programs:
            name = p.get("name", "")
            inc  = p.get("seven_d", "N/A")
            prog_lines.append(f'{name}: {inc}')
        prog_text  = ("\n" + "\n".join(prog_lines)) if prog_lines else ""
        m10n_block = (
            f'\n\n<b>Monetization</b>\n'
            f'<blockquote>'
            f'Balance  {balance}\n'
            f'7 Days   {total_7d}'
            f'{prog_text}'
            f'</blockquote>'
        )
    except Exception as e:
        clog("INFO", f"Monetization error: {e}")
        m10n_block = ""

    tg_html(
        f'<b>{fmt_label(lbl)}</b>' + (f' · <a href="{avatar}">Avatar</a>' if avatar else "") + "\n"
        f'\n<b>Profile</b>\n'
        f'<blockquote>'
        f'ID       {info.get("user_id", "")}\n'
        f'Region   {info.get("region", "")} · {info.get("language", "")}{verified}{private}\n'
        f'Follow   {info.get("follower_count", 0):,}\n'
        f'Following  {info.get("following_count", 0):,}\n'
        f'Likes    {info.get("heart_count", 0):,}\n'
        f'Videos   {info.get("video_count", 0):,}\n'
        f'Digg     {info.get("digg_count", 0):,}'
        f'</blockquote>'
        + aff_block
        + m10n_block
        + (f'\n\n<b>Bio</b>\n<blockquote>{sig}</blockquote>' if sig else '')
    )


# ─── Upload queue ─────────────────────────────────────────────────────────────

def build_upload_queue(folder, uploaded, use_product, videos_per_product):
    all_videos = [v for v in get_videos(folder) if v.name not in uploaded]
    if not all_videos:
        return []
    if not use_product:
        return list(all_videos)

    grouped = {}
    order   = []
    for v in all_videos:
        pid = extract_product_id(str(v)) or "__none__"
        if pid not in grouped:
            grouped[pid] = []
            order.append(pid)
        grouped[pid].append(v)

    queue = []
    while any(grouped[pid] for pid in order):
        for pid in order:
            if not grouped[pid]:
                continue
            batch        = grouped[pid][:videos_per_product]
            grouped[pid] = grouped[pid][videos_per_product:]
            queue.extend(batch)
    return queue


# ─── Account worker ───────────────────────────────────────────────────────────

def account_worker(acc, semaphore=None):
    cookies            = acc["cookies"]
    folder             = acc["folder"]
    label              = acc["label"]
    use_product        = acc.get("use_product", False)
    videos_per_hour    = acc.get("videos_per_hour", 1)
    videos_per_product = acc.get("videos_per_product", 3)
    captions           = load_captions()
    hashtags           = load_hashtags()
    cap_index          = 0
    upload_queue       = []

    db_data  = db_load()
    uploaded = (
        {e["video"] for e in db_data.get(label, {}).get("uploaded", [])} |
        {e["video"] for e in db_data.get(label, {}).get("failed", [])}
    )

    clog(label, f"Started | Folder: {folder} | {len(get_videos(folder))} videos | {videos_per_hour}/h | DB: {len(uploaded)} done")

    while not stop_event.is_set():
        slots   = load_time_config()
        in_slot = is_in_slot(slots)[0]

        if not in_slot:
            upload_queue = []
            wait_until_next_slot(slots, label)
            continue

        if not upload_queue:
            upload_queue = build_upload_queue(folder, uploaded, use_product, videos_per_product)

        if not upload_queue:
            clog(label, "No videos left. Waiting for new files...")
            while not stop_event.is_set():
                tg_html(
                    f'<b>[NO VIDEO] {fmt_label(label)}</b>\n'
                    f'\n<b>Folder</b>\n'
                    f'<blockquote>{folder}</blockquote>\n'
                    f'Add videos to the folder to continue.'
                )
                for _ in range(3600):
                    if stop_event.is_set():
                        return
                    if [v for v in get_videos(folder) if v.name not in uploaded]:
                        clog(label, "Detected new videos. Resuming...")
                        upload_queue = build_upload_queue(folder, uploaded, use_product, videos_per_product)
                        break
                    time.sleep(1)
                else:
                    continue
                break
            if not upload_queue:
                continue

        video = upload_queue.pop(0)
        if video.name in uploaded:
            continue

        pid, product_title = get_product_info(str(video), use_product, cookies)
        caption            = product_title if product_title else captions[cap_index % len(captions)]
        cap_index         += 1
        music              = load_music_for_slot()

        clog(label, f"Uploading: {video.name} | Caption: {caption}")

        base          = 3600 / videos_per_hour
        jitter        = random.uniform(-0.2, 0.2) * base
        wait          = max(60, int(base + jitter))
        next_upload_t = (datetime.now() + timedelta(seconds=wait)).strftime("%H:%M")

        try:
            if semaphore:
                semaphore.acquire()
            try:
                result = upload_video(cookies, str(video), caption, hashtags, music, pid, product_title)
            finally:
                if semaphore:
                    semaphore.release()

            uploaded.add(video.name)
            videos_left = len([v for v in get_videos(folder) if v.name not in uploaded])

            if result.get("success"):
                url = result.get("video_url", "")
                db_record_upload(label, video.name, url, True)
                clog(label, f"OK: {url} | Left: {videos_left} | Next: {next_upload_t}")

                if acc.get("delete_after"):
                    try:
                        os.remove(str(video))
                        clog(label, f"Deleted: {video.name}")
                    except Exception as de:
                        clog(label, f"Delete failed: {de}")

                _info   = acc.get("info", {})
                _avatar = _info.get("avatar", "")
                est     = estimate_finish(videos_left, videos_per_hour, load_time_config())
                tg_html(
                    f'<b>{fmt_label(label)}</b>' + (f' · <a href="{_avatar}">Avatar</a>' if _avatar else "") + "\n"
                    f'\n<b>Video</b>\n'
                    f'<blockquote><a href="{url}">{video.name}</a>\n'
                    f'{caption}</blockquote>\n'
                    f'\n<b>Stats</b>\n'
                    f'<blockquote>Follow:  {_info.get("follower_count", 0):,}\n'
                    f'Likes:   {_info.get("heart_count", 0):,}\n'
                    f'Left:    {videos_left}\n'
                    f'Next:    {next_upload_t}\n'
                    f'ETA:     {est}</blockquote>'
                )
            else:
                err = result.get("error", "unknown")
                db_record_upload(label, video.name, "", False)
                clog(label, f"Failed: {err} | Response: {json.dumps(result, ensure_ascii=False)}")
                tg_html(
                    f'<b>[FAILED] {fmt_label(label)}</b>\n'
                    f'\n<b>Video</b>\n'
                    f'<blockquote>{video.name}</blockquote>\n'
                    f'\n<b>Error</b>\n'
                    f'<blockquote>{err}</blockquote>'
                )

        except Exception as e:
            clog(label, f"Exception: {e}")
            tg_html(
                f'<b>[ERROR] {fmt_label(label)}</b>\n'
                f'\n<b>Video</b>\n'
                f'<blockquote>{video.name}</blockquote>\n'
                f'\n<b>Error</b>\n'
                f'<blockquote>{e}</blockquote>'
            )
            wait = 300

        for _ in range(int(wait)):
            if stop_event.is_set():
                return
            time.sleep(1)

    clog(label, "Worker stopped.")


# ─── Setup ────────────────────────────────────────────────────────────────────

def setup():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

    print("=" * 50)
    print("  TikTok Account Nurture Tool")
    print("=" * 50)

    if not os.path.exists(TIME_CONFIG):
        with open(TIME_CONFIG, "w", encoding="utf-8") as f:
            json.dump({"slots": ["07:00 - 14:00", "18:00 - 23:00"]}, f, indent=2)
        print(f"[!] Created {TIME_CONFIG} with defaults. Edit if needed.\n")

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Enter Telegram credentials (Enter to skip):")
        tok = input("  Bot Token: ").strip()
        cid = input("  Chat ID  : ").strip()
        if tok and cid:
            TELEGRAM_TOKEN   = tok
            TELEGRAM_CHAT_ID = cid

    if not os.path.exists(COOKIES_FILE):
        open(COOKIES_FILE, "w").close()
        print(f"[!] Created {COOKIES_FILE} — one cookie string per line (one account).")
        input("  Fill it in then press Enter...")

    with open(COOKIES_FILE, encoding="utf-8") as f:
        raw_cookies = [l.strip() for l in f if l.strip()]

    if not raw_cookies:
        print("Cookies.txt is empty!")
        exit(1)

    print(f"\nLoaded {len(raw_cookies)} accounts from Cookies.txt")
    print("Fetching account info...\n")

    acc_list = []
    for i, ck in enumerate(raw_cookies):
        try:
            info  = get_account_info(ck)
            label = f"{info.get('nickname', '?')} (@{info.get('unique_id', '?')})"
            acc_list.append({"cookies": ck, "info": info, "label": label})
            print(f"  [{i+1}] OK  {label}")
        except Exception as e:
            label = f"Account #{i+1}"
            acc_list.append({"cookies": ck, "info": {}, "label": label})
            print(f"  [{i+1}] ERR {label}: {e}")

    print()
    delete_after = input("  Delete video after successful upload? (y/n): ").strip().lower() == "y"
    use_product  = input("  Attach product to videos? (y/n): ").strip().lower() == "y"

    vph_input       = input("  Videos per hour? (default 1): ").strip()
    videos_per_hour = int(vph_input) if vph_input.isdigit() and int(vph_input) > 0 else 1
    print(f"  -> {videos_per_hour} video/h\n")

    videos_per_product = 3
    if use_product:
        vpp_input          = input("  Max consecutive videos per product? (default 3): ").strip()
        videos_per_product = int(vpp_input) if vpp_input.isdigit() and int(vpp_input) > 0 else 3
        print(f"  -> {videos_per_product} videos/product\n")

    _load_music_ids()
    if _music_ids:
        print(f"  Loaded {len(_music_ids)} music ids from Music.json\n")

    for acc in acc_list:
        while True:
            folder = input(f"  Video folder for [{acc['label']}]: ").strip().strip('"')
            if os.path.isdir(folder):
                print(f"    -> {len(get_videos(folder))} videos\n")
                acc["folder"]             = folder
                acc["delete_after"]       = delete_after
                acc["use_product"]        = use_product
                acc["videos_per_hour"]    = videos_per_hour
                acc["videos_per_product"] = videos_per_product
                break
            print("    Folder not found, try again.")

    return acc_list


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    accounts = setup()
    slots    = load_time_config()
    captions = load_captions()
    hashtags = load_hashtags()

    print("=" * 50)
    print("Summary:")
    for acc in accounts:
        print(f"  {acc['label']} — {len(get_videos(acc['folder']))} videos")
    print(f"\nSlots   : {' | '.join(s['label'] for s in slots)}")
    print(f"Captions: {len(captions)} lines")
    print(f"Hashtags: {hashtags}")
    print("=" * 50)
    input("\nPress Enter to start (Ctrl+C to stop)...\n")

    tg_html(
        f'<b>Nurture Tool started</b>\n'
        f'Accounts: {len(accounts)}\n'
        + "\n".join(f"  {a['label']} — {len(get_videos(a['folder']))} videos" for a in accounts)
        + f"\nSlots: {' | '.join(s['label'] for s in slots)}"
    )

    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        threading.Thread(
            target=tg_listener,
            args=(lambda: accounts, load_time_config),
            daemon=True,
        ).start()

    threads = []
    for acc in accounts:
        t = threading.Thread(target=account_worker, args=(acc, None), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()
        for t in threads:
            t.join(timeout=5)
        tg_html("<b>Nurture Tool stopped.</b>")
        print("Stopped.")


if __name__ == "__main__":
    main()
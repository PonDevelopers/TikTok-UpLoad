# TikTok Upload API

> 🇬🇧 [English](#english) · 🇻🇳 [Tiếng Việt](#tiếng-việt)

---

# English

A hosted API service for automated TikTok video uploads — supports music, affiliate products, caption/hashtag, account info, affiliate dashboard, and a ready-to-use upload bot with Telegram notifications.

> **API endpoint:** `https://lechaukhaapi.eu.org`  
> **Get an API key:** contact [@lekha8899](https://t.me/lekha8899) on Telegram

---

## Overview

The server is hosted and managed by the admin. You only need an API key to start using it — no server setup required.

There are two ways to use this service:

| Option | Best for |
|---|---|
| **Use the API directly** | Developers who want to build their own tool or integrate into an existing workflow |
| **Run `Api.py`** | Users who want a ready-made bot with scheduling, multi-account, and Telegram notifications |

---

## Authentication

Every request requires an API key in the header:

```
X-API-Key: your_key_here
```

Missing or invalid key returns:

```json
{ "success": false, "error": "Missing API key." }
{ "success": false, "error": "Invalid API key." }
```

---

## Privacy & Security

Your cookies and data are **never stored** on the server.

Here's exactly what happens when you make a request:

1. Your request arrives at the API
2. The server uses your cookies **in memory** to call TikTok on your behalf
3. The result is returned to you
4. Everything is discarded — no database, no logs, no files written

The server has no persistence layer. It cannot "remember" your cookies between requests even if it wanted to. Each request is fully isolated.

> **In short:** your cookies pass through the server like water through a pipe — used once, gone immediately.

---

## API Reference

### `POST /account` — Get account info

**Body (JSON):**
```json
{ "cookies": "sessionid=abc;msToken=xyz;..." }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "7593337830941541392",
    "unique_id": "m.anhzin",
    "nickname": "Minh Anh",
    "sec_uid": "MS4wLjABAAAA...",
    "signature": "bio here",
    "region": "VN",
    "language": "vi",
    "verified": false,
    "private": false,
    "avatar": "https://p16-sign.tiktokcdn.com/...",
    "follower_count": 12400,
    "following_count": 310,
    "heart_count": 98000,
    "video_count": 47,
    "digg_count": 520
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/account \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "sessionid=abc;msToken=xyz"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/account",
    headers={"X-API-Key": "your_key_here"},
    json={"cookies": "sessionid=abc;msToken=xyz;..."},
)
print(r.json())
```

---

### `POST /affiliate` — Get affiliate dashboard

**Body (JSON):**
```json
{ "cookies": "sessionid=abc;msToken=xyz;..." }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "today": {
      "gmv": "0₫",
      "items_sold": "0",
      "commission": "0₫"
    },
    "last_7_days": {
      "gmv": "813,8K ₫",
      "items_sold": "8",
      "commission": "34,6K ₫"
    }
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/affiliate \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "sessionid=abc;msToken=xyz"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/affiliate",
    headers={"X-API-Key": "your_key_here"},
    json={"cookies": "sessionid=abc;msToken=xyz;..."},
)
print(r.json())
```

> ⚠️ Only works for accounts that have joined TikTok Shop Affiliate. Returns an error for non-affiliate accounts.

---

### `POST /music` — Get music info by ID

**Body (JSON):**
```json
{ "music_id": "7426731559144672001" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "music_id_string": "7426731559144672001",
    "music_title": "Song Title",
    "music_author": "Artist Name",
    "music_album": "",
    "music_url": "https://v16m.tiktokcdn.com/..."
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/music \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"music_id": "7426731559144672001"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/music",
    headers={"X-API-Key": "your_key_here"},
    json={"music_id": "7426731559144672001"},
)
print(r.json())
```

> ⚠️ `music_url` expires within a few hours. Always call `/music` right before uploading — never cache the URL.

---

### `POST /product` — Get product info

**Body (JSON):**
```json
{ "cookies": "sessionid=abc;...", "product_id": "1730987654321" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product_id": "1730987654321",
    "title": "Product Name",
    "price": "150.000đ",
    "shop_name": "Shop ABC",
    "in_stock": true
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/product \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "sessionid=abc;...", "product_id": "1730987654321"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/product",
    headers={"X-API-Key": "your_key_here"},
    json={"cookies": "sessionid=abc;...", "product_id": "1730987654321"},
)
print(r.json())
```

---

### `POST /upload` — Upload video

**Form-data fields:**

| Field | Required | Description |
|---|---|---|
| `cookies` | ✅ | TikTok cookie string |
| `video` | ✅ | Video file (mp4 / mov) |
| `caption` | ❌ | Video caption text |
| `hashtags` | ❌ | Comma-separated hashtags: `viral,fyp` |
| `visibility` | ❌ | `0`=public, `1`=friends, `2`=private (default `0`) |
| `allow_comment` | ❌ | `1`=on, `0`=off (default `1`) |
| `allow_content_reuse` | ❌ | `1`=on, `0`=off (default `1`) |
| `music` | ❌ | JSON string of the object returned by `/music` |
| `product_id` | ❌ | TikTok Shop product ID |
| `product_title` | ❌ | Product display name |

**Response:**
```json
{
  "success": true,
  "item_id": "7627057259327147272",
  "video_url": "https://www.tiktok.com/@m.anhzin/video/7627057259327147272",
  "account": {
    "user_id": "7593337830941541392",
    "unique_id": "m.anhzin",
    "nickname": "Minh Anh",
    "follower_count": 12400,
    "heart_count": 98000
  }
}
```

**cURL — basic upload:**
```bash
curl -X POST https://lechaukhaapi.eu.org/upload \
  -H "X-API-Key: your_key_here" \
  -F "cookies=sessionid=abc;msToken=xyz" \
  -F "caption=Check this out" \
  -F "hashtags=viral,fyp" \
  -F "video=@video.mp4"
```

**Python — basic upload:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/upload",
    headers={"X-API-Key": "your_key_here"},
    data={
        "cookies":  "sessionid=abc;msToken=xyz;...",
        "caption":  "Check this out",
        "hashtags": "viral,fyp,trending",
    },
    files={"video": open("video.mp4", "rb")},
)
print(r.json())
```

**Python — upload with music:**
```python
import requests, json

HEADERS = {"X-API-Key": "your_key_here"}

music = requests.post(
    "https://lechaukhaapi.eu.org/music",
    headers=HEADERS,
    json={"music_id": "7426731559144672001"},
).json()["data"]

r = requests.post(
    "https://lechaukhaapi.eu.org/upload",
    headers=HEADERS,
    data={
        "cookies":  "sessionid=abc;msToken=xyz;...",
        "caption":  "Check this out",
        "hashtags": "viral,fyp",
        "music":    json.dumps(music),
    },
    files={"video": open("video.mp4", "rb")},
)
print(r.json())
```

**Python — upload with product:**
```python
import requests, json

HEADERS = {"X-API-Key": "your_key_here"}

product = requests.post(
    "https://lechaukhaapi.eu.org/product",
    headers=HEADERS,
    json={"cookies": "sessionid=abc;...", "product_id": "1730987654321"},
).json()["data"]

r = requests.post(
    "https://lechaukhaapi.eu.org/upload",
    headers=HEADERS,
    data={
        "cookies":       "sessionid=abc;msToken=xyz;...",
        "caption":       "Get yours now",
        "hashtags":      "tiktokshop,viral",
        "product_id":    product["product_id"],
        "product_title": product["title"],
    },
    files={"video": open("video.mp4", "rb")},
)
print(r.json())
```

---

## Default video settings

| Parameter | Value |
|---|---|
| Resolution | 1080 × 1920 (9:16) |
| FPS | 30 |
| Format | mp4 |

---

## Common errors

| Error | Cause |
|---|---|
| `Missing API key.` | `X-API-Key` header not sent |
| `Invalid API key.` | Key not valid or expired — contact admin to renew |
| `cookies required` | Missing cookies field |
| `video file required` | Missing video file |
| `TikTok rejected` | Expired or invalid TikTok cookies |
| `Product not found` | product_id does not exist or does not belong to your shop |
| `Music not found` | Invalid or unavailable music ID |
| `Affiliate API error` | Account has not joined TikTok Shop Affiliate |

---

## Ready-made bot — Api.py

Don't want to write code? `Api.py` is a ready-to-use automation bot built on top of this API. It handles scheduling, multi-account rotation, music/caption/hashtag rotation, product attachment, and Telegram notifications — no coding required.

### Requirements

```bash
pip install requests
```

### Quick start

```bash
python Api.py
```

On first run, the bot walks you through the full setup interactively.

Set your API key in `Api.py` before running:

```python
API_KEY = "your_key_here"
```

### File structure

| File | Description |
|---|---|
| `Cookies.txt` | One TikTok cookie string per line (one account per line) |
| `Caption.txt` | One caption per line — rotated per upload |
| `Hashtag.txt` | Comma or newline separated hashtags |
| `Music.json` | JSON array of music IDs — rotated automatically, index saved across restarts |
| `Time.json` | Upload time slots config |
| `Database.json` | Auto-generated upload history |
| `log.log` | Full upload log (auto-generated) |

### Time.json

```json
{ "slots": ["07:00 - 14:00", "18:00 - 23:00"] }
```

### Music.json

```json
["7426731559144672001", "7391234567890123456"]
```

### Video file naming (product mode)

Name files as `{product_id}_{anything}.mp4` to auto-attach a product:

```
1730987654321_clip1.mp4
1730987654321_clip2.mp4
```

### Interactive setup prompts

| Prompt | Description |
|---|---|
| Telegram Bot Token / Chat ID | To receive upload notifications (press Enter to skip) |
| Delete video after upload? | `y` = delete file after successful upload |
| Attach product to videos? | `y` = read product ID from filename |
| Videos per hour | Upload rate per account (default `1`) |
| Max consecutive videos per product | Product mode only (default `3`) |
| Video folder per account | Path to the folder containing `.mp4` / `.mov` files |

### Upload scheduling

- Uploads only happen within configured time slots
- Interval = `3600 / videos_per_hour` seconds ± 20% random jitter (minimum 60s)
- If no videos remain, the bot polls every hour and resumes automatically when new files appear

### Telegram bot commands

| Command | Description |
|---|---|
| `/check` | Current status — active slot, uploads done/failed, videos left, ETA per account |
| `/info` | List accounts, reply with a number to see full details including affiliate balance |

---

## Contact

Telegram: [@lekha8899](https://t.me/lekha8899)  
© 2026 **Le Chau Kha** — All rights reserved.

---

---

# Tiếng Việt

Dịch vụ API upload TikTok tự động — hỗ trợ nhạc, sản phẩm affiliate, caption/hashtag, thông tin tài khoản, dashboard affiliate, và bot upload sẵn có với thông báo Telegram.

> **API endpoint:** `https://lechaukhaapi.eu.org`  
> **Mua API key:** liên hệ [@lekha8899](https://t.me/lekha8899) trên Telegram

---

## Tổng quan

Server được admin host và quản lý sẵn. Bạn chỉ cần API key là dùng được ngay — không cần cài đặt server.

Có hai cách sử dụng:

| Cách | Phù hợp với |
|---|---|
| **Gọi API trực tiếp** | Developer muốn tự code tool hoặc tích hợp vào workflow có sẵn |
| **Chạy `Api.py`** | Người dùng muốn bot có sẵn với lên lịch, đa tài khoản và thông báo Telegram |

---

## Xác thực

Mọi request đều cần API key trong header:

```
X-API-Key: your_key_here
```

Thiếu hoặc sai key trả về:

```json
{ "success": false, "error": "Missing API key." }
{ "success": false, "error": "Invalid API key." }
```

---

## Bảo mật & Quyền riêng tư

Cookies và dữ liệu của bạn **không bao giờ được lưu lại** trên server.

Đây là những gì xảy ra khi bạn gửi request:

1. Request của bạn tới API
2. Server dùng cookies của bạn **trong bộ nhớ tạm** để gọi TikTok thay bạn
3. Kết quả được trả về cho bạn
4. Tất cả bị xóa ngay — không database, không log, không file nào được ghi lại

Server không có bộ nhớ lâu dài. Nó không thể "nhớ" cookies của bạn giữa các lần request dù có muốn. Mỗi request hoạt động hoàn toàn độc lập.

> **Nói ngắn gọn:** cookies của bạn đi qua server như nước qua ống — dùng xong là mất ngay.

---

## API Reference

### `POST /account` — Lấy thông tin tài khoản

**Body (JSON):**
```json
{ "cookies": "sessionid=abc;msToken=xyz;..." }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "7593337830941541392",
    "unique_id": "m.anhzin",
    "nickname": "Minh Anh",
    "sec_uid": "MS4wLjABAAAA...",
    "signature": "bio ở đây",
    "region": "VN",
    "language": "vi",
    "verified": false,
    "private": false,
    "avatar": "https://p16-sign.tiktokcdn.com/...",
    "follower_count": 12400,
    "following_count": 310,
    "heart_count": 98000,
    "video_count": 47,
    "digg_count": 520
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/account \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "sessionid=abc;msToken=xyz"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/account",
    headers={"X-API-Key": "your_key_here"},
    json={"cookies": "sessionid=abc;msToken=xyz;..."},
)
print(r.json())
```

---

### `POST /affiliate` — Lấy doanh thu affiliate

**Body (JSON):**
```json
{ "cookies": "sessionid=abc;msToken=xyz;..." }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "today": {
      "gmv": "0₫",
      "items_sold": "0",
      "commission": "0₫"
    },
    "last_7_days": {
      "gmv": "813,8K ₫",
      "items_sold": "8",
      "commission": "34,6K ₫"
    }
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/affiliate \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "sessionid=abc;msToken=xyz"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/affiliate",
    headers={"X-API-Key": "your_key_here"},
    json={"cookies": "sessionid=abc;msToken=xyz;..."},
)
print(r.json())
```

> ⚠️ Chỉ hoạt động với tài khoản đã tham gia TikTok Shop Affiliate. Trả về lỗi nếu tài khoản chưa đăng ký affiliate.

---

### `POST /music` — Lấy thông tin nhạc theo ID

**Body (JSON):**
```json
{ "music_id": "7426731559144672001" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "music_id_string": "7426731559144672001",
    "music_title": "Tên bài hát",
    "music_author": "Tên nghệ sĩ",
    "music_album": "",
    "music_url": "https://v16m.tiktokcdn.com/..."
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/music \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"music_id": "7426731559144672001"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/music",
    headers={"X-API-Key": "your_key_here"},
    json={"music_id": "7426731559144672001"},
)
print(r.json())
```

> ⚠️ `music_url` có thời hạn vài giờ. Luôn gọi `/music` ngay trước khi upload — không cache URL lại.

---

### `POST /product` — Lấy thông tin sản phẩm

**Body (JSON):**
```json
{ "cookies": "sessionid=abc;...", "product_id": "1730987654321" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product_id": "1730987654321",
    "title": "Tên sản phẩm",
    "price": "150.000đ",
    "shop_name": "Shop ABC",
    "in_stock": true
  }
}
```

**cURL:**
```bash
curl -X POST https://lechaukhaapi.eu.org/product \
  -H "X-API-Key: your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "sessionid=abc;...", "product_id": "1730987654321"}'
```

**Python:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/product",
    headers={"X-API-Key": "your_key_here"},
    json={"cookies": "sessionid=abc;...", "product_id": "1730987654321"},
)
print(r.json())
```

---

### `POST /upload` — Upload video

**Form-data fields:**

| Field | Bắt buộc | Mô tả |
|---|---|---|
| `cookies` | ✅ | Cookie TikTok dạng string |
| `video` | ✅ | File video (mp4 / mov) |
| `caption` | ❌ | Caption video |
| `hashtags` | ❌ | Hashtag cách nhau bằng dấu phẩy: `viral,fyp` |
| `visibility` | ❌ | `0`=public, `1`=friends, `2`=private (mặc định `0`) |
| `allow_comment` | ❌ | `1`=bật, `0`=tắt (mặc định `1`) |
| `allow_content_reuse` | ❌ | `1`=bật, `0`=tắt (mặc định `1`) |
| `music` | ❌ | JSON string của object trả về từ `/music` |
| `product_id` | ❌ | ID sản phẩm TikTok Shop |
| `product_title` | ❌ | Tên sản phẩm hiển thị |

**Response:**
```json
{
  "success": true,
  "item_id": "7627057259327147272",
  "video_url": "https://www.tiktok.com/@m.anhzin/video/7627057259327147272",
  "account": {
    "user_id": "7593337830941541392",
    "unique_id": "m.anhzin",
    "nickname": "Minh Anh",
    "follower_count": 12400,
    "heart_count": 98000
  }
}
```

**cURL — upload cơ bản:**
```bash
curl -X POST https://lechaukhaapi.eu.org/upload \
  -H "X-API-Key: your_key_here" \
  -F "cookies=sessionid=abc;msToken=xyz" \
  -F "caption=Video hay quá" \
  -F "hashtags=viral,fyp" \
  -F "video=@video.mp4"
```

**Python — upload cơ bản:**
```python
import requests

r = requests.post(
    "https://lechaukhaapi.eu.org/upload",
    headers={"X-API-Key": "your_key_here"},
    data={
        "cookies":  "sessionid=abc;msToken=xyz;...",
        "caption":  "Video hay quá",
        "hashtags": "viral,fyp,xuhuong",
    },
    files={"video": open("video.mp4", "rb")},
)
print(r.json())
```

**Python — upload kèm nhạc:**
```python
import requests, json

HEADERS = {"X-API-Key": "your_key_here"}

music = requests.post(
    "https://lechaukhaapi.eu.org/music",
    headers=HEADERS,
    json={"music_id": "7426731559144672001"},
).json()["data"]

r = requests.post(
    "https://lechaukhaapi.eu.org/upload",
    headers=HEADERS,
    data={
        "cookies":  "sessionid=abc;msToken=xyz;...",
        "caption":  "Video hay quá",
        "hashtags": "viral,fyp",
        "music":    json.dumps(music),
    },
    files={"video": open("video.mp4", "rb")},
)
print(r.json())
```

**Python — upload kèm sản phẩm:**
```python
import requests, json

HEADERS = {"X-API-Key": "your_key_here"}

product = requests.post(
    "https://lechaukhaapi.eu.org/product",
    headers=HEADERS,
    json={"cookies": "sessionid=abc;...", "product_id": "1730987654321"},
).json()["data"]

r = requests.post(
    "https://lechaukhaapi.eu.org/upload",
    headers=HEADERS,
    data={
        "cookies":       "sessionid=abc;msToken=xyz;...",
        "caption":       "Mua ngay nào",
        "hashtags":      "tiktokshop,viral",
        "product_id":    product["product_id"],
        "product_title": product["title"],
    },
    files={"video": open("video.mp4", "rb")},
)
print(r.json())
```

---

## Cấu hình video mặc định

| Thông số | Giá trị |
|---|---|
| Resolution | 1080 × 1920 (9:16) |
| FPS | 30 |
| Format | mp4 |

---

## Lỗi thường gặp

| Lỗi | Nguyên nhân |
|---|---|
| `Missing API key.` | Chưa gửi header `X-API-Key` |
| `Invalid API key.` | Key không hợp lệ hoặc hết hạn — liên hệ admin để gia hạn |
| `cookies required` | Thiếu field cookies |
| `video file required` | Thiếu file video |
| `TikTok rejected` | Cookie hết hạn hoặc không hợp lệ |
| `Product not found` | product_id không tồn tại hoặc không thuộc shop của bạn |
| `Music not found` | Music ID không hợp lệ hoặc không khả dụng |
| `Affiliate API error` | Tài khoản chưa tham gia TikTok Shop Affiliate |

---

## Bot có sẵn — Api.py

Không muốn tự code? `Api.py` là bot upload tự động được xây dựng sẵn trên API này. Hỗ trợ lên lịch theo khung giờ, đa tài khoản, xoay vòng nhạc/caption/hashtag, gắn sản phẩm tự động và thông báo Telegram — không cần code.

### Yêu cầu

```bash
pip install requests
```

### Khởi động nhanh

```bash
python Api.py
```

Lần đầu chạy, bot sẽ hỏi các thông số cấu hình tự động. Điền API key vào `Api.py` trước khi chạy:

```python
API_KEY = "your_key_here"
```

### Cấu trúc file

| File | Mô tả |
|---|---|
| `Cookies.txt` | Mỗi dòng 1 cookie TikTok (1 tài khoản) |
| `Caption.txt` | Mỗi dòng 1 caption — xoay vòng theo lượt upload |
| `Hashtag.txt` | Hashtag cách nhau bằng dấu phẩy hoặc xuống dòng |
| `Music.json` | Mảng JSON các music ID — xoay vòng tự động, lưu index qua các lần restart |
| `Time.json` | Cấu hình khung giờ upload |
| `Database.json` | Lịch sử upload (tự tạo) |
| `log.log` | Log đầy đủ quá trình upload (tự tạo) |

### Time.json

```json
{ "slots": ["07:00 - 14:00", "18:00 - 23:00"] }
```

### Music.json

```json
["7426731559144672001", "7391234567890123456"]
```

### Đặt tên file video (chế độ sản phẩm)

Đặt tên file dạng `{product_id}_{bất kỳ}.mp4` để tự động gắn sản phẩm:

```
1730987654321_clip1.mp4
1730987654321_clip2.mp4
```

### Câu hỏi khi khởi động lần đầu

| Câu hỏi | Mô tả |
|---|---|
| Telegram Bot Token / Chat ID | Để nhận thông báo upload (Enter để bỏ qua) |
| Xóa video sau khi upload? | `y` = xóa file sau khi upload thành công |
| Gắn sản phẩm vào video? | `y` = đọc product ID từ tên file |
| Videos per hour | Tốc độ upload mỗi tài khoản (mặc định `1`) |
| Max videos mỗi sản phẩm liên tiếp | Chỉ ở chế độ sản phẩm (mặc định `3`) |
| Thư mục video cho từng tài khoản | Đường dẫn thư mục chứa file `.mp4` / `.mov` |

### Lên lịch upload

- Bot chỉ upload trong các khung giờ đã cấu hình
- Khoảng cách giữa các lượt = `3600 / videos_per_hour` giây ± 20% ngẫu nhiên (tối thiểu 60 giây)
- Hết video thì bot chờ và tự tiếp tục khi có file mới trong thư mục

### Lệnh Telegram bot

| Lệnh | Mô tả |
|---|---|
| `/check` | Trạng thái hiện tại — slot, đã đăng/lỗi, còn lại, ETA từng tài khoản |
| `/info` | Liệt kê tài khoản, gõ số để xem chi tiết bao gồm doanh thu affiliate |

---

## Liên hệ

Telegram: [@lekha8899](https://t.me/lekha8899)  
© 2026 **Le Chau Kha** — All rights reserved.

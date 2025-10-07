import os
import json
import threading
import time
from flask import Flask, jsonify, request
from pyppeteer import launch
import asyncio

# =========================================================
# 🧱 防睡眠 Flask 伺服器（獨立埠）
# =========================================================
keep_alive_app = Flask("keep_alive")

@keep_alive_app.route('/')
def keep_alive_home():
    return "✅ Keep-alive server is running!", 200

def run_keep_alive():
    port = int(os.getenv("KEEP_ALIVE_PORT", 8081))
    keep_alive_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_keep_alive)
    t.daemon = True
    t.start()

# =========================================================
# ⚙️ 主 Flask API
# =========================================================
app = Flask(__name__)
POSTS_FILE = "posts.json"
COOKIE_FILE = "fb_state.json"


# =========================================================
# 📂 儲存與讀取
# =========================================================
def save_posts(posts):
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def load_posts():
    if not os.path.exists(POSTS_FILE):
        return []
    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


# =========================================================
# 🤖 Facebook 爬蟲主程式（使用 Pyppeteer）
# =========================================================
async def scrape_facebook_async():
    print("🚀 啟動 Facebook 爬蟲")

    if not os.path.exists(COOKIE_FILE):
        print("❌ 缺少 fb_state.json，請先上傳 Cookie")
        return

    fb_url = os.getenv("FB_PAGE_URL", "https://www.facebook.com/appledaily.tw/posts")

    try:
        print("🧱 啟動 Chromium (Pyppeteer 模式)...")
        browser = await launch(
            headless=True,
            executablePath="/usr/bin/google-chrome",
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = await browser.newPage()

        # 載入 cookie
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookie_data = json.load(f)
        cookies = cookie_data.get("cookies", [])
        await page.setCookie(*cookies)

        print(f"🌍 前往：{fb_url}")
        await page.goto(fb_url, {"timeout": 120000, "waitUntil": "networkidle2"})

        # 模擬滾動以載入更多內容
        for i in range(3):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await asyncio.sleep(3)

        posts = []
        elements = await page.querySelectorAll('div[role="article"]')
        for el in elements:
            text_el = await el.querySelector('div[data-ad-preview="message"], span[dir="auto"]')
            text = await page.evaluate("(el) => el.innerText", text_el) if text_el else ""
            img_el = await el.querySelector('img[src*="scontent"]')
            img = await page.evaluate("(el) => el.src", img_el) if img_el else None
            if text or img:
                posts.append({
                    "content": text.strip(),
                    "image": img,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })

        await browser.close()
        print(f"✅ 完成，擷取 {len(posts)} 則貼文")
        save_posts(posts)
        return posts

    except Exception as e:
        print(f"❌ 執行錯誤：{e}")


def scrape_facebook():
    asyncio.run(scrape_facebook_async())


# =========================================================
# 📡 API 路由
# =========================================================
@app.route("/upload", methods=["POST"])
def upload_cookie():
    try:
        data = request.get_json()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Cookie 已更新")
        return jsonify({"message": "✅ Cookie 已更新"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/run", methods=["GET"])
def run_scraper():
    threading.Thread(target=scrape_facebook).start()
    return jsonify({"message": "🚀 爬蟲已啟動"}), 200


@app.route("/status", methods=["GET"])
def status():
    posts = load_posts()
    return jsonify({
        "fb_state.json": os.path.exists(COOKIE_FILE),
        "posts_count": len(posts),
        "recent_posts": posts[-3:] if posts else []
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Railway FB Scraper (Pyppeteer)",
        "status": "online"
    }), 200


# =========================================================
# 🚀 主程式啟動
# =========================================================
if __name__ == "__main__":
    os.environ["KEEP_ALIVE_PORT"] = "8081"
    keep_alive()

    port = int(os.getenv("PORT", 5000))
    print(f"🌐 主 Flask 服務啟動於 port {port}")
    app.run(host="0.0.0.0", port=port, use_reloader=False)

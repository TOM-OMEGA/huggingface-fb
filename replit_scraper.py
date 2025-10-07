import os
import json
import threading
import time
import requests
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
from threading import Thread

# -------------------------------
# 🧱 Replit 防睡眠功能
# -------------------------------
keep_alive_app = Flask("keep_alive")

@keep_alive_app.route('/')
def keep_alive_home():
    return "✅ Replit keep-alive server is running!", 200

def run_keep_alive():
    port = int(os.getenv("KEEP_ALIVE_PORT", 8080))
    keep_alive_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_keep_alive)
    t.daemon = True
    t.start()

# -------------------------------
# ⚙️ 主應用設定
# -------------------------------
app = Flask(__name__)
POSTS_FILE = "posts.json"
COOKIE_FILE = "fb_state.json"
RENDER_API_URL = os.getenv("RENDER_API_URL", "https://carrotbot-z-x-n-information-1-yeqq.onrender.com")
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")

def notify_render(event, data=None):
    """向 Render 回報狀態"""
    if not RENDER_API_KEY:
        print("⚠️ 未設定 RENDER_API_KEY，略過回報")
        return
    try:
        payload = {"event": event, "data": data or {}, "key": RENDER_API_KEY}
        r = requests.post(f"{RENDER_API_URL}/crawler_report", json=payload, timeout=10)
        print(f"📡 回報 {event} 至 Render ({r.status_code})")
    except Exception as e:
        print(f"❌ 回報 Render 失敗：{e}")

# -------------------------------
# 📂 貼文儲存
# -------------------------------
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

# -------------------------------
# 🤖 Facebook 爬蟲
# -------------------------------
def scrape_facebook():
    print("🚀 啟動 Facebook 爬蟲")
    notify_render("crawler_started")

    if not os.path.exists(COOKIE_FILE):
        print("❌ 缺少 fb_state.json，請先上傳 Cookie")
        notify_render("crawler_error", {"error": "missing_cookie"})
        return

    fb_url = os.getenv("FB_PAGE_URL", "https://www.facebook.com/appledaily.tw/posts")

    try:
        with sync_playwright() as p:
            print("🧱 啟動 Chromium...")
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(storage_state=COOKIE_FILE)
            page = context.new_page()
            page.goto(fb_url, timeout=120000)
            page.wait_for_load_state("networkidle")

            for _ in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(5000)

            posts = []
            articles = page.query_selector_all('div[role="article"]')
            for post in articles:
                text_el = post.query_selector('div[data-ad-preview="message"], span[dir="auto"]')
                text = text_el.inner_text().strip() if text_el else ""
                img_el = post.query_selector('img[src*=\"scontent\"]')
                img = img_el.get_attribute("src") if img_el else None
                if text or img:
                    posts.append({
                        "content": text,
                        "image": img,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })

            browser.close()
            print(f"✅ 完成，擷取 {len(posts)} 則貼文")
            save_posts(posts)
            notify_render("crawler_finished", {"count": len(posts)})
            return posts

    except Exception as e:
        print(f"❌ 執行錯誤：{e}")
        notify_render("crawler_error", {"error": str(e)})

# -------------------------------
# 📡 API 路由
# -------------------------------
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
        "service": "Replit FB Scraper",
        "status": "online"
    }), 200

# -------------------------------
# 🚀 主程式
# -------------------------------
if __name__ == "__main__":
    keep_alive()
    notify_render("crawler_online")
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Flask 啟動於 port {port}")
    app.run(host="0.0.0.0", port=port)

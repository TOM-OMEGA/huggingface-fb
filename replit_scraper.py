import os
import json
import threading
import time
import requests
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
from threading import Thread

# =========================================================
# 🧱 Replit 防睡眠功能（使用獨立 Flask port）
# =========================================================
keep_alive_app = Flask("keep_alive")

@keep_alive_app.route('/')
def keep_alive_home():
    return "✅ Replit keep-alive server is running!", 200

@keep_alive_app.route('/ping')
def keep_alive_ping():
    return "pong", 200

def run_keep_alive():
    port = int(os.getenv("KEEP_ALIVE_PORT", 8081))  # ⚙️ 改為不與主服務衝突的 port
    try:
        keep_alive_app.run(host="0.0.0.0", port=port)
    except OSError:
        print(f"⚠️ keep_alive port {port} 已被占用，略過啟動。")

def keep_alive():
    """啟動防睡眠背景 Flask 伺服器"""
    t = Thread(target=run_keep_alive)
    t.daemon = True
    t.start()


# =========================================================
# ⚙️ 主應用設定
# =========================================================
app = Flask(__name__)
POSTS_FILE = "posts.json"
COOKIE_FILE = "fb_state.json"


# =========================================================
# 📂 儲存/讀取貼文
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
# 🤖 Facebook 爬蟲主程式
# =========================================================
def scrape_facebook():
    print("🚀 啟動 Facebook 爬蟲")

    if not os.path.exists(COOKIE_FILE):
        print("❌ 缺少 fb_state.json，請先上傳 Cookie")
        return

    fb_url = os.getenv("FB_PAGE_URL", "https://www.facebook.com/appledaily.tw/posts")

    try:
        with sync_playwright() as p:
            print("🧱 啟動 Chromium...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                storage_state=COOKIE_FILE,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/121.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            print(f"🌍 載入粉專：{fb_url}")
            page.goto(fb_url, timeout=120000)
            page.wait_for_load_state("networkidle", timeout=60000)

            for i in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(5000)

            posts = []
            articles = page.query_selector_all('div[role="article"]')
            for post in articles:
                text_el = post.query_selector('div[data-ad-preview="message"], span[dir="auto"]')
                text = text_el.inner_text().strip() if text_el else ""
                img_el = post.query_selector('img[src*="scontent"]')
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
            return posts

    except Exception as e:
        print(f"❌ 執行錯誤：{e}")


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
        "service": "Replit FB Scraper",
        "status": "online"
    }), 200


# =========================================================
# 🚀 主程式啟動點
# =========================================================
if __name__ == "__main__":
    # ✅ 啟動防睡眠伺服器（固定使用 8081）
    os.environ["KEEP_ALIVE_PORT"] = "8081"
    keep_alive()

    # ✅ Replit 會自動提供 PORT 環境變數（外部可存取的 port）
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 主 Flask 服務啟動於 port {port}")

    # ✅ 禁用 reloader 避免自動重啟造成衝突
    app.run(host="0.0.0.0", port=port, use_reloader=False)

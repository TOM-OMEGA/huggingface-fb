import os
import json
import sqlite3
import threading
import time
import requests
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright

app = Flask(__name__)
DB_PATH = "fb_posts.db"

# -------------------------------
# 🧱 防休眠保活線程
# -------------------------------
def keep_alive():
    url = os.getenv("KEEP_ALIVE_URL")
    if not url:
        return
    while True:
        try:
            requests.get(url)
        except:
            pass
        time.sleep(300)  # 每5分鐘ping一次
threading.Thread(target=keep_alive, daemon=True).start()

# -------------------------------
# 📂 初始化資料庫
# -------------------------------
def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_post(content, image=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO posts (content, image) VALUES (?, ?)", (content, image))
    conn.commit()
    conn.close()

# -------------------------------
# 🤖 爬蟲主程式
# -------------------------------
def scrape_facebook():
    print("🚀 開始執行 Facebook 爬蟲")
    ensure_db()

    if not os.path.exists("fb_state.json"):
        print("❌ 找不到 fb_state.json，請先上傳 Cookie")
        return

    try:
        with sync_playwright() as p:
            print("🧱 啟動 Chromium...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            context = browser.new_context(
                storage_state="fb_state.json",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/121.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            fb_url = os.getenv("FB_PAGE_URL", "https://www.facebook.com/appledaily.tw/posts")
            print(f"🌍 正在載入：{fb_url}")
            page.goto(fb_url, timeout=120000)
            page.wait_for_load_state("networkidle", timeout=60000)

            # 模擬滾動載入更多內容
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
                    save_post(text, img)
                    posts.append({"content": text, "image": img})

            browser.close()
            print(f"✅ 完成，擷取 {len(posts)} 則貼文")
            return posts

    except Exception as e:
        print(f"❌ 執行錯誤：{e}")

# -------------------------------
# 📡 路由：啟動爬蟲
# -------------------------------
@app.route("/run", methods=["GET"])
def run_scraper():
    thread = threading.Thread(target=scrape_facebook)
    thread.start()
    return jsonify({"message": "爬蟲啟動成功"}), 200

# -------------------------------
# 📡 路由：上傳 Cookie
# -------------------------------
@app.route("/upload", methods=["POST"])
def upload_cookie():
    try:
        data = request.get_json()
        with open("fb_state.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Cookie 已更新")
        return jsonify({"message": "✅ Cookie 已更新"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# 📡 路由：查詢貼文狀態
# -------------------------------
@app.route("/status", methods=["GET"])
def status():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT content, image, timestamp FROM posts ORDER BY id DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()
    posts = [{"content": r[0], "image": r[1], "timestamp": r[2]} for r in rows]
    return jsonify(posts), 200

# -------------------------------
# 📡 健康檢查首頁
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Railway FB Scraper",
        "status": "online"
    }), 200

# -------------------------------
# 🚀 啟動 Flask
# -------------------------------
def run():
    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Flask 啟動於 port {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run()

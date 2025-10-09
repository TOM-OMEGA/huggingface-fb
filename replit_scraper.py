import os
import json
import time
import asyncio
import threading
from flask import Flask, jsonify, request, abort
from pyppeteer import launch

# =========================================================
# 🧱 Keep-alive Flask（防 Render 睡眠）
# =========================================================
keep_alive_app = Flask("keep_alive")

@keep_alive_app.route('/')
def keep_alive_home():
    return "✅ Keep-alive server is running!", 200

def run_keep_alive():
    port = int(os.getenv("KEEP_ALIVE_PORT", 8081))
    print(f"🌙 Keep-alive Flask running on port {port}")
    keep_alive_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_keep_alive)
    t.daemon = True
    t.start()

# =========================================================
# ⚙️ 主 Flask 服務
# =========================================================
app = Flask(__name__)

COOKIE_FILE = "/tmp/fb_state.json"
POSTS_FILE = "/tmp/posts.json"
API_KEY = os.getenv("RENDER_API_KEY")
FB_URL = os.getenv("FB_PAGE_URL", "https://www.facebook.com/LARPtimes/")

# =========================================================
# 🧩 初始化 Cookie
# =========================================================
def init_cookie_from_env():
    fb_cookie = os.getenv("FB_COOKIES")
    if fb_cookie and not os.path.exists(COOKIE_FILE):
        try:
            data = json.loads(fb_cookie)
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("✅ FB Cookie 已從環境變數寫入 /tmp/fb_state.json")
        except Exception as e:
            print(f"⚠️ 無法解析 FB_COOKIES: {e}")

# =========================================================
# 🔒 驗證安全金鑰
# =========================================================
@app.before_request
def verify_api_key():
    if request.path in ["/", "/status"]:
        return
    key = request.headers.get("Authorization")
    if not key or key != f"Bearer {API_KEY}":
        print(f"⛔ 未授權的存取：{request.path}")
        abort(401)

# =========================================================
# 📂 資料存取
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
# 🔍 自動偵測 Chrome 路徑
# =========================================================
def find_chrome_path():
    paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/opt/google/chrome/chrome"
    ]
    for path in paths:
        if os.path.exists(path):
            print(f"🧭 偵測到 Chrome 執行路徑：{path}")
            return path
    print("⚠️ 未找到 Chrome，請確認 Dockerfile 有安裝 google-chrome-stable")
    return None

# =========================================================
# 🕷️ Facebook 爬蟲主程式
# =========================================================
async def scrape_facebook_async():
    print(f"🚀 開始爬取：{FB_URL}")

    if not os.path.exists(COOKIE_FILE):
        print("❌ 找不到 fb_state.json，請先上傳 Cookie")
        return []

    try:
        chrome_path = find_chrome_path()
        if not chrome_path:
            return []

        print("🧱 啟動 Chromium (Pyppeteer 模式)...")
        browser = await launch(
            headless=True,
            executablePath=chrome_path,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1280,800"
            ]
        )
        page = await browser.newPage()

        # 移除 "navigator.webdriver" 屬性 (反爬蟲防護)
        await page.evaluateOnNewDocument("""
            () => {
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            }
        """)

        # 載入 Cookie
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookie_data = json.load(f)
        cookies = cookie_data.get("cookies", [])
        await page.setCookie(*cookies)

        print(f"🌍 前往：{FB_URL}")
        await page.goto(FB_URL, {"timeout": 120000, "waitUntil": "networkidle2"})

        html = await page.content()
        if "登入 Facebook" in html or "login" in page.url:
            print("⚠️ Cookie 已失效或未登入狀態")
            await browser.close()
            return []

        # 滾動載入更多內容
        for i in range(3):
            print(f"🔄 滾動載入第 {i+1}/3 次...")
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await asyncio.sleep(4)

        posts = []
        elements = await page.querySelectorAll('div[role="article"]')
        print(f"📑 偵測到 {len(elements)} 則貼文元素")

        for idx, el in enumerate(elements):
            try:
                text_el = await el.querySelector('div[data-ad-preview="message"], span[dir="auto"]')
                text = await page.evaluate("(el) => el.innerText", text_el) if text_el else ""
                img_el = await el.querySelector('img[src*=\"scontent\"]')
                img = await page.evaluate("(el) => el.src", img_el) if img_el else None
                if text or img:
                    posts.append({
                        "content": text.strip(),
                        "image": img,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print(f"📝 第 {idx+1} 則貼文擷取成功")
            except Exception as e:
                print(f"⚠️ 第 {idx+1} 則貼文解析錯誤: {e}")

        await browser.close()
        print(f"✅ 爬取完成，共 {len(posts)} 則貼文")
        save_posts(posts)
        return posts

    except Exception as e:
        print(f"❌ 爬蟲執行錯誤：{e}")
        return []

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
    print("🟢 收到 /run 請求，啟動背景爬蟲執行緒")

    def worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        posts = loop.run_until_complete(scrape_facebook_async())
        print(f"✅ 爬蟲完成，共 {len(posts)} 則貼文")
        loop.close()

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"message": "🚀 爬蟲已啟動"}), 200


@app.route("/status", methods=["GET"])
def get_status():
    posts = load_posts()
    return jsonify({
        "fb_state.json": os.path.exists(COOKIE_FILE),
        "posts_count": len(posts),
        "recent_posts": posts[-3:] if posts else []
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Render FB Scraper (Pyppeteer)",
        "status": "online"
    }), 200

# =========================================================
# 🚀 主程式
# =========================================================
if __name__ == "__main__":
    os.environ["KEEP_ALIVE_PORT"] = "8081"
    keep_alive()
    init_cookie_from_env()

    port = int(os.getenv("PORT", 5000))
    print(f"🌐 主 Flask 服務啟動於 port {port}")
    app.run(host="0.0.0.0", port=port, use_reloader=False)

import os
import json
import time
import traceback
from flask import Flask, jsonify, request, abort
import threading

# =========================================================
# 🧱 Keep-alive Flask（防 Render 睡眠）
# =========================================================
keep_alive_app = Flask("keep_alive")

@keep_alive_app.route('/')
def keep_alive_home():
    return "✅ Keep-alive server is running!", 200

def run_keep_alive():
    port = int(os.getenv("KEEP_ALIVE_PORT", 8081))
    print(f"🌙 Keep-alive Flask running on port {port}", flush=True)
    keep_alive_app.run(host="0.0.0.0", port=port)

def keep_alive():
    threading.Thread(target=run_keep_alive, daemon=True).start()

# =========================================================
# ⚙️ 主 Flask 服務
# =========================================================
app = Flask(__name__)

COOKIE_FILE = "/tmp/fb_state.json"
POSTS_FILE = "/tmp/posts.json"
API_KEY = os.getenv("RENDER_API_KEY")

# =========================================================
# 🧩 初始化 Cookie（如果環境變數中有）
# =========================================================
def init_cookie_from_env():
    fb_cookie = os.getenv("FB_COOKIES")
    if fb_cookie and not os.path.exists(COOKIE_FILE):
        try:
            data = json.loads(fb_cookie)
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("✅ FB Cookie 已從環境變數寫入 /tmp/fb_state.json", flush=True)
        except Exception as e:
            print(f"⚠️ 無法解析 FB_COOKIES: {e}", flush=True)

# =========================================================
# 🔒 驗證安全金鑰
# =========================================================
@app.before_request
def verify_api_key():
    if request.path in ["/", "/status"]:
        return
    key = request.headers.get("Authorization")
    if not key or key != f"Bearer {API_KEY}":
        print(f"⛔ 未授權的存取：{request.path}", flush=True)
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
# 📡 API 路由
# =========================================================

@app.route("/upload", methods=["POST"])
def upload_cookie():
    """讓你更新 Cookie"""
    try:
        data = request.get_json()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Cookie 已更新", flush=True)
        return jsonify({"message": "✅ Cookie 已更新"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload_posts", methods=["POST"])
def upload_posts():
    """讓你的本機爬蟲上傳結果"""
    try:
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({"error": "資料格式錯誤，應該是一個貼文列表"}), 400
        save_posts(data)
        print(f"✅ 收到並儲存 {len(data)} 則貼文", flush=True)
        return jsonify({"message": f"已儲存 {len(data)} 則貼文"}), 200
    except Exception as e:
        print(f"❌ 上傳貼文失敗: {e}", flush=True)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/status", methods=["GET"])
def get_status():
    """查詢目前儲存的貼文狀態"""
    posts = load_posts()
    return jsonify({
        "fb_state.json": os.path.exists(COOKIE_FILE),
        "posts_count": len(posts),
        "recent_posts": posts[-3:] if posts else []
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Render FB Scraper Server",
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
    print(f"🌐 主 Flask 服務啟動於 port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, use_reloader=False)

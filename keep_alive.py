# keep_alive.py
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Replit keep-alive server is running!", 200

@app.route('/ping')
def ping():
    return "pong", 200

def run():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    """在背景啟動 Flask web server，讓 Replit 維持活著狀態"""
    t = Thread(target=run)
    t.daemon = True
    t.start()

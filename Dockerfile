# ==================================================
# 🐍 使用官方 Python 3.11-slim 作為基底
# ==================================================
FROM python:3.11-slim

# ==================================================
# 📦 安裝系統依賴 + Google Chrome
# ==================================================
RUN apt-get update && apt-get install -y \
    wget gnupg unzip \
    ca-certificates \
    fonts-liberation \
    libasound2t64 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libxshmfence1 \
    libxss1 \
    libxext6 \
    libxfixes3 \
    libdrm2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# 🌐 安裝 Google Chrome（穩定版）
# ==================================================
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /usr/share/keyrings/google-linux-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] \
    http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 顯示 Chrome 版本以供除錯
RUN google-chrome --version || true

# ==================================================
# 🧰 安裝 Python 套件
# ==================================================
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ==================================================
# 📂 複製應用程式原始碼
# ==================================================
COPY . .

# ==================================================
# ⚙️ 設定環境變數與 PORT
# ==================================================
ENV PORT=5000
ENV PYTHONUNBUFFERED=1
EXPOSE 5000

# ==================================================
# 🚀 啟動主程式
# ==================================================
# 如果你的主程式檔名是 fb_scraper.py，這裡改成那個
CMD ["python3", "replit_scraper.py"]

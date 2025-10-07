# ------------------------------
# ✅ 使用穩定版 Python 3.11
# ------------------------------
FROM python:3.11-slim

# ------------------------------
# 安裝 Google Chrome 與基本依賴
# ------------------------------
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl fonts-liberation xdg-utils \
    libnss3 libnspr4 libxss1 libx11-xcb1 libxcomposite1 \
    libxrandr2 libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxdamage1 libgbm1 libxkbcommon0 \
    libxshmfence1 libgtk-3-0 libpangocairo-1.0-0 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Chrome（官方 deb）
RUN wget -q -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./chrome.deb && rm chrome.deb

# ------------------------------
# 設定工作目錄
# ------------------------------
WORKDIR /app

# ------------------------------
# 複製 requirements 並安裝套件
# ------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# 複製應用程式原始碼
# ------------------------------
COPY . .

# ------------------------------
# 設定環境變數
# ------------------------------
ENV PORT=8080
EXPOSE 8080

# ------------------------------
# 啟動程式
# ------------------------------
RUN chmod +x start.sh
CMD ["bash", "start.sh"]

# 使用官方 Python 3.11 slim 作為基底
FROM python:3.11-slim

# ==================================================
# 安裝 Google Chrome + Pyppeteer 依賴
# ==================================================
RUN apt-get update && apt-get install -y wget gnupg unzip fonts-liberation libasound2t64 libnspr4 libnss3 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0 libxshmfence1 libxss1 libxext6 libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Google Chrome（最新版）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && rm -rf /var/lib/apt/lists/*

# ==================================================
# 安裝 Python 套件
# ==================================================
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==================================================
# 複製原始碼
# ==================================================
COPY . .

# ==================================================
# 環境變數
# ==================================================
ENV PORT=8080
EXPOSE 8080

# ==================================================
# 啟動主程式
# ==================================================
CMD ["python3", "replit_scraper.py"]

# 使用官方 Python 3.11 slim 版本作為基礎
FROM python:3.11-slim

# ------------------------------
# 系統套件安裝（Playwright 需要的依賴）
# ------------------------------
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# 設定工作目錄
# ------------------------------
WORKDIR /app

# ------------------------------
# 複製並安裝 Python 套件
# ------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# 複製程式碼到容器
# ------------------------------
COPY . .

# ------------------------------
# 安裝 Chromium（給 Playwright 用）
# ------------------------------
RUN playwright install --with-deps chromium

# ------------------------------
# 設定環境變數
# ------------------------------
ENV PORT=8080
EXPOSE 8080

# ------------------------------
# 啟動 Flask 伺服器
# ------------------------------
CMD ["python3", "replit_scraper.py"]

# ------------------------------
# ✅ 使用穩定版 Python 3.11（Playwright 支援最佳）
# ------------------------------
FROM python:3.11-slim

# ------------------------------
# 安裝 Playwright 依賴與常用工具
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
# 複製 requirements.txt 並安裝 Python 套件
# ------------------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# 複製應用程式原始碼
# ------------------------------
COPY . .

# ------------------------------
# 安裝 Chromium（Playwright 使用）
# ------------------------------
RUN playwright install --with-deps chromium

# ------------------------------
# 設定環境變數
# ------------------------------
ENV PORT=8080
EXPOSE 8080

# ------------------------------
# ✅ 使用 start.sh 啟動（可自動重啟）
# ------------------------------
RUN chmod +x start.sh
CMD ["bash", "start.sh"]

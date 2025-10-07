# ------------------------------
# ✅ 使用官方 Playwright Python 基底映像（支援 Chromium）
# ------------------------------
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# ------------------------------
# 🔁 強制重建層：每次 commit 都會重建 Docker cache
# ------------------------------
ARG CACHEBUST=$(date +%s)

# ------------------------------
# 設定工作目錄
# ------------------------------
WORKDIR /app

# ------------------------------
# 複製 requirements.txt 並安裝 Python 套件
# ------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# 複製專案檔案
# ------------------------------
COPY . .

# ------------------------------
# 安裝系統相依套件（特別補上 libnspr4、libgtk、libxshmfence1）
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnspr4 libgtk-3-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# ✅ 強制重新安裝 Playwright Chromium 並清除舊快取
# ------------------------------
RUN rm -rf /root/.cache/ms-playwright && \
    playwright install --with-deps chromium

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

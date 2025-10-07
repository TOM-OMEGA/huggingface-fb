# ------------------------------
# ✅ 使用官方 Playwright Python 基底映像
# ------------------------------
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

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
# 安裝系統相依套件（額外補 libnspr4、libgtk）
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnspr4 libgtk-3-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# ✅ 強制重新安裝 Chromium 並清除舊快取
# ------------------------------
ARG CACHEBUSTER=1
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
# Force rebuild Tue Oct  7 02:29:42 PM UTC 2025

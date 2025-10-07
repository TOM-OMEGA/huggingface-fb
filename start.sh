#!/bin/bash
echo "🚀 啟動 Replit FB Scraper + Keep Alive 服務..."
while true
do
  python3 replit_scraper.py
  echo "⚠️ 程式崩潰，10 秒後重新啟動..."
  sleep 10
done

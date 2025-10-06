#!/usr/bin/env bash
echo "🚀 啟動 Flask + Discord Bot 中..."

# 顯示環境資訊
python3 --version
echo "📂 檔案列表："
ls -al

# 啟動 Flask 伺服器（背景執行）
echo "🌐 啟動 Flask 伺服器..."
gunicorn fb_scraper:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 --log-level debug --access-logfile - &

# 啟動 Discord Bot
echo "🤖 啟動 Discord Bot..."
python3 bot.py

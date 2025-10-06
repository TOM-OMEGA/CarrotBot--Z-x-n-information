#!/bin/bash

echo "🚀 start.sh 已執行"

# ✅ 安裝 Playwright Chromium（Render 無頭環境）
export PLAYWRIGHT_BROWSERS_PATH=0
playwright install chromium

# ✅ 顯示目前目錄與檔案
echo "📂 目前目錄內容："
ls -l

# ✅ 背景啟動 Discord Bot
echo "✅ 啟動 Discord Bot 中..."
python bot.py &

# ✅ 啟動 Flask 主程式
echo "✅ 啟動 Flask 主程式中..."
python fb_scraper.py

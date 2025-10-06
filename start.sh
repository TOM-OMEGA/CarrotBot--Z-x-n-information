#!/bin/bash

# ✅ 設定 Playwright 安裝路徑（Render 支援）
export PLAYWRIGHT_BROWSERS_PATH=0

# ✅ 安裝 Playwright Chromium（Render 無頭環境）
playwright install chromium

# ⚠️ Render 無法執行 GUI 登入，略過 login_once.py
echo "⚠️ Render 無法執行 login_once.py，請在本機登入後上傳 cookie"

# ✅ 背景啟動 Discord Bot（保持在線）
echo "✅ 啟動 Discord Bot 中..."
python bot.py &

# ✅ 啟動 Flask 主程式（Render 主進程）
echo "✅ 啟動 Flask 主程式中..."
python fb_scraper.py

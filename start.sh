#!/bin/bash

# ✅ 設定 Playwright 安裝路徑（Render 支援）
export PLAYWRIGHT_BROWSERS_PATH=0

# ✅ 安裝 Playwright 瀏覽器（只執行一次）
playwright install chromium

# ✅ 執行一次性登入（可選，若已用 /refresh-login 可略過）
python login_once.py || echo "⚠️ login_once.py 執行失敗，略過"

# ✅ 背景啟動 Discord Bot（保持在線）
python bot.py &

# ✅ 啟動 Flask 應用（Render 主進程）
python fb_scraper.py

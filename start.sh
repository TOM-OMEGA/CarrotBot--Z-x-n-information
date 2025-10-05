#!/bin/bash

# ✅ 設定 Playwright 安裝路徑（Render 支援）
export PLAYWRIGHT_BROWSERS_PATH=0

# ✅ 安裝 Playwright 瀏覽器（只執行一次）
playwright install chromium

# ✅ 執行一次性登入（可選，若已用 /refresh-login 可略過）
python login_once.py || echo "⚠️ login_once.py 執行失敗，略過"

# ✅ 啟動 Flask 應用（Render 會保持此進程）
python fb_scraper.py

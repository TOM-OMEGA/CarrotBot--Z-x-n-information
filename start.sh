#!/usr/bin/env bash
echo "🚀 啟動 Flask 伺服器中..."

# 確保資料庫存在
python3 -c "from fb_scraper import init_db; init_db()"

# 安裝 Playwright Chromium（避免初次啟動缺失）
playwright install chromium

# 啟動 gunicorn（Render 會自動注入 PORT 環境變數）
exec gunicorn fb_scraper:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120

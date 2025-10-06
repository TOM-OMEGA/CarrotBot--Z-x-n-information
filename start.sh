#!/usr/bin/env bash
echo "🚀 啟動 Flask 伺服器中..."

# 初始化資料庫（如果有）
python3 -c "from fb_scraper import init_db; init_db()" 2>/dev/null || echo "略過 init_db"

# 用 gunicorn 啟動 Flask（Render 會自動注入 PORT）
exec gunicorn fb_scraper:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 --log-level debug --access-logfile -

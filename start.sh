#!/usr/bin/env bash
echo "🚀 啟動 Flask + Discord Bot 中..."

python3 --version
echo "📂 檔案列表："
ls -al

# 安裝 Playwright 執行需要的系統依賴
echo "🧩 安裝 Playwright 瀏覽器依賴中..."
npx playwright install-deps chromium || \
apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm-dev \
    libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 \
    libxfixes3 libcups2 \
    && rm -rf /var/lib/apt/lists/*

# 確保瀏覽器已安裝
echo "🧱 安裝 Chromium..."
playwright install chromium

# 啟動 Flask + Discord Bot（合併版）
python3 run_combined.py

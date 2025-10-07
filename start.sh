#!/usr/bin/env bash
echo "🚀 啟動 Flask + Discord Bot 中..."

python3 --version
echo "📂 檔案列表："
ls -al

echo "🧩 安裝 Playwright 依賴中..."
apt-get update && apt-get install -y \
    wget libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm-dev \
    libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 \
    libxfixes3 libcups2 fonts-liberation libappindicator3-1 \
    xdg-utils libdrm2 libxshmfence1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

echo "🧱 安裝 Chromium..."
python3 -m playwright install chromium

echo "🚀 啟動 Flask + Discord Bot..."
python3 run_combined.py

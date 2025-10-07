#!/usr/bin/env bash
echo "🚀 啟動 Flask + Discord Bot 中..."
python3 --version
ls -al

echo "🧱 安裝必要系統套件..."
apt-get update && apt-get install -y \
    wget libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm-dev \
    libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 \
    libxfixes3 libcups2 fonts-liberation libappindicator3-1 \
    xdg-utils libdrm2 libxshmfence1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

echo "🚀 啟動主程式 fb_scraper.py"
python3 fb_scraper.py

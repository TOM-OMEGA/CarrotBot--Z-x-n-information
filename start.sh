#!/usr/bin/env bash
echo "🚀 啟動 Flask + Discord Bot 中..."

# 強制使用 Python 3.11
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
else
    PYTHON_CMD=python3
fi

$PYTHON_CMD --version
ls -al

echo "🧱 安裝必要系統套件..."
apt-get update && apt-get install -y \
    wget libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm-dev \
    libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 \
    libxfixes3 libcups2 fonts-liberation libappindicator3-1 \
    xdg-utils libdrm2 libxshmfence1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

echo "📦 安裝 Python 套件..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel
$PYTHON_CMD -m pip install -r requirements.txt

echo "🚀 啟動主程式 fb_scraper.py"
$PYTHON_CMD fb_scraper.py

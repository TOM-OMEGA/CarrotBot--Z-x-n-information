# 使用與 Replit 相容的 Python 版本
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統相依套件（Playwright 執行 Chromium 需要）
RUN apt-get update && apt-get install -y \
    wget curl libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm-dev \
    libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 \
    libxfixes3 libcups2 fonts-liberation libappindicator3-1 \
    xdg-utils libdrm2 libxshmfence1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 複製檔案
COPY . .

# 安裝 Python 套件
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    playwright install chromium

# 開放 Flask 預設埠
EXPOSE 10000

# ------------------------------
# 啟動 Discord Bot
# ------------------------------
CMD ["python3", "bot.py"]

# --- 使用 Python 3.11 環境 ---
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（Playwright 需要）
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 複製程式
COPY . .

# 安裝 Python 套件
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN playwright install chromium

# 啟動 Flask
CMD ["bash", "start.sh"]

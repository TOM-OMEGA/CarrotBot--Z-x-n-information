FROM python:3.11-slim

# 安裝系統依賴 (lxml 需要)
RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製需求檔並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 啟動指令
CMD ["python", "main.py"]

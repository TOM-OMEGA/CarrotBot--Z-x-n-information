#!/usr/bin/env bash
echo "🚀 啟動 Flask + Discord Bot 中..."

python3 --version
echo "📂 檔案列表："
ls -al

# 直接執行主控程式 (整合 Flask + Bot)
python3 run_combined.py

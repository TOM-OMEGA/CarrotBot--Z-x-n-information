import threading
import os
from fb_scraper import app
import discord
from bot import client  # 匯入 bot.py 裡的 client 實例

def run_discord():
    print("🤖 啟動 Discord Bot...")
    client.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    # 先啟動 Discord Bot（非阻塞）
    threading.Thread(target=run_discord, daemon=True).start()

    # 再啟動 Flask（主線程、Render 監聽 port）
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 啟動 Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

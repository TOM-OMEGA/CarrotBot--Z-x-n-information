import threading
import os
from fb_scraper import app
from bot import client

def run_discord():
    print("🤖 啟動 Discord Bot...")
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ 未設定 DISCORD_BOT_TOKEN")
        return
    client.run(token)

if __name__ == "__main__":
    # 先啟動 Discord Bot（背景執行）
    discord_thread = threading.Thread(target=run_discord, daemon=True)
    discord_thread.start()

    # 啟動 Flask 伺服器（主線程，Render 偵測用）
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 啟動 Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

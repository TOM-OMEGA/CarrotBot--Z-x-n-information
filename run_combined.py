import threading
import os
from fb_scraper import app
import bot

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 啟動 Flask on port {port}")
    app.run(host="0.0.0.0", port=port)

def run_discord():
    print("🤖 啟動 Discord Bot...")
    bot.client.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    t1 = threading.Thread(target=run_flask)
    t1.start()

    t2 = threading.Thread(target=run_discord)
    t2.start()

    t1.join()
    t2.join()

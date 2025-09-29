import os
import asyncio
import discord
import sqlite3
from facebook_scraper import get_posts
from flask import Flask
from threading import Thread

# ===== Discord Bot =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的 Discord 頻道 ID
FB_PAGES = ["appledaily.tw", "setnews.tw", "udn.com"]  # 這裡放多個粉專 ID 或名稱
DB_FILE = "posts.db"

# ===== SQLite 初始化 =====
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS posts (post_id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_post_sent(post_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM posts WHERE post_id=?", (post_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_post(post_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO posts (post_id) VALUES (?)", (post_id,))
    conn.commit()
    conn.close()

# ===== 抓取多粉專貼文 =====
async def fetch_facebook_posts():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    while not client.is_closed():
        try:
            for page in FB_PAGES:
                for post in get_posts(page, pages=1):
                    post_id = post['post_id']
                    if not is_post_sent(post_id):
                        save_post(post_id)
                        text = post.get('text', '')[:500]
                        url = post.get('post_url', '')
                        await channel.send(f"📢 {page} 新貼文：\n{text}\n🔗 {url}")
                    break  # 只抓最新一篇
        except Exception as e:
            print(f"抓取失敗: {e}")

        await asyncio.sleep(600)  # 每 10 分鐘檢查一次

@client.event
async def on_ready():
    print(f"✅ 已登入 {client.user}")
    init_db()
    client.loop.create_task(fetch_facebook_posts())

# ===== Flask 假 Web Server (給 Render + UptimeRobot) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask).start()

# ===== 啟動 Bot =====
client.run(os.getenv("DISCORD_TOKEN"))

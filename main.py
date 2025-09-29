import os
import asyncio
import discord
import sqlite3
from facebook_scraper import get_posts
from keep_alive import keep_alive, bot_status

# ===== Discord Bot =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的頻道 ID
FB_PAGES = ["appledaily.tw", "setnews.tw", "udn.com"]
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

    if channel is None:
        print("❌ 找不到指定的 Discord 頻道，請確認 DISCORD_CHANNEL_ID 是否正確")
        return

    print("✅ 背景任務已啟動，開始定期檢查粉專貼文...")

    while not client.is_closed():
        for page in FB_PAGES:
            try:
                print(f"🔎 正在檢查粉專: {page}")
                bot_status["last_check"] = f"正在檢查 {page}"

                for post in get_posts(page, pages=1):
                    post_id = post.get("post_id")
                    text = post.get("text", "")
                    url = post.get("post_url", "")

                    if not post_id:
                        print(f"⚠️ {page} 沒有抓到 post_id，可能是抓取失敗")
                        continue

                    print(f"📌 抓到貼文 {post_id}，前50字: {text[:50]}...")

                    if not is_post_sent(post_id):
                        save_post(post_id)
                        msg = f"📢 {page} 新貼文：\n{text[:300]}...\n🔗 {url}"
                        await channel.send(msg)
                        bot_status["last_post"] = f"{page} {post_id}"
                        print(f"✅ 已發送到 Discord 頻道 {channel.name}")
                    else:
                        print(f"⏩ {page} 的貼文 {post_id} 已經發送過，跳過")

                    break  # 只抓最新一篇
            except Exception as e:
                print(f"❌ 抓取 {page} 失敗: {e}")

        print("💤 本輪檢查結束，10 分鐘後再檢查")
        await asyncio.sleep(600)

@client.event
async def on_ready():
    add_log(f"✅ 已登入 {client.user}")
    bot_status["logged_in"] = True
    init_db()
    client.loop.create_task(fetch_facebook_posts())

async def fetch_facebook_posts():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        add_log("❌ 找不到指定的 Discord 頻道，請確認 DISCORD_CHANNEL_ID 是否正確")
        return

    add_log("✅ 背景任務已啟動，開始定期檢查粉專貼文...")

    while not client.is_closed():
        for page in FB_PAGES:
            try:
                add_log(f"🔎 正在檢查粉專: {page}")
                bot_status["last_check"] = f"正在檢查 {page}"

                for post in get_posts(page, pages=1):
                    post_id = post.get("post_id")
                    text = post.get("text", "")
                    url = post.get("post_url", "")

                    if not post_id:
                        add_log(f"⚠️ {page} 沒有抓到 post_id，可能是抓取失敗")...

# ===== 啟動 Flask 假 Web Server =====
keep_alive()

# ===== 啟動 Bot =====
client.run(os.getenv("DISCORD_TOKEN"))

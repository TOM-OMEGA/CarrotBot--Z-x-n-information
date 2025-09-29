import os
import asyncio
import discord
import sqlite3
from facebook_scraper import get_posts
from keep_alive import keep_alive, bot_status, add_log

# ===== Discord Bot =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的頻道 ID
FB_PAGES = ["appledaily.tw", "setnews.tw", "udn.com"]
DB_FILE = "posts.db"

# ===== SQLite =====
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

# ===== Fetch Facebook posts =====
async def fetch_facebook_posts():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        add_log("❌ Cannot find the Discord channel.")
        return

    add_log("✅ Background task started.")
    # 測試訊息：確認背景任務真的有跑
    await channel.send("🔔 Background task is running!")

    while not client.is_closed():
        for page in FB_PAGES:
            try:
                add_log(f"Checking page: {page}")
                bot_status["last_check"] = f"Checking {page}"

                for post in get_posts(page, pages=1):
                    post_id = post.get("post_id")
                    text = post.get("text", "")
                    url = post.get("post_url", "")

                    if not post_id:
                        add_log(f"WARNING: {page} returned no post_id")
                        continue

                    add_log(f"Found post {post_id}, preview: {text[:50]}...")

                    if not is_post_sent(post_id):
                        save_post(post_id)
                        msg = f"[{page}] New post:\n{text[:300]}...\nLink: {url}"
                        await channel.send(msg)
                        bot_status["last_post"] = f"{page} {post_id}"
                        add_log(f"Post {post_id} sent to Discord channel {channel.name}")
                    else:
                        add_log(f"Skipped {page} post {post_id}, already sent")

                    break  # only latest post
            except Exception as e:
                add_log(f"ERROR: Failed to fetch {page}: {e}")

        add_log("Cycle finished. Sleeping 10 minutes...")
        await asyncio.sleep(600)

@client.event
async def on_ready():
    add_log(f"Logged in as {client.user}")
    bot_status["logged_in"] = True
    init_db()

    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online and ready!")  # 測試訊息
        add_log("Test message sent to Discord.")
    else:
        add_log("❌ Channel not found. Check DISCORD_CHANNEL_ID.")

    client.loop.create_task(fetch_facebook_posts())

# ===== Start Flask server =====
keep_alive()

# ===== Start Bot =====
client.run(os.getenv("DISCORD_TOKEN"))

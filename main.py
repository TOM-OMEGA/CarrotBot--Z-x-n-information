import os
import asyncio
import discord
import sqlite3
import json
from facebook_scraper import get_posts
from keep_alive import keep_alive, bot_status, add_log

intents = discord.Intents.default()
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的頻道 ID
PAGES_FILE = "pages.json"  # 儲存粉專清單的檔案
DB_FILE = "posts.db"
COOKIES_PATH = "cookies.json"
COOKIE_CHECK_INTERVAL = 21600  # 預設 6 小時 (秒)

# ===== 載入粉專清單 =====
if os.path.exists(PAGES_FILE):
    with open(PAGES_FILE, "r", encoding="utf-8") as f:
        FB_PAGES = json.load(f)
else:
    FB_PAGES = ["LARPtimes", "setnews.tw", "udn.com"]  # 預設清單

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

# ===== Background Task: 抓取貼文 =====
async def fetch_facebook_posts():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        add_log("❌ Cannot find the Discord channel.")
        return

    add_log("✅ Background task started.")
    await channel.send("🔔 Background task is running with cookies check!")

    while not client.is_closed():
        for page in FB_PAGES:
            await fetch_page_posts(channel, page)
        add_log("Cycle finished. Sleeping 10 minutes...")
        await asyncio.sleep(600)

# ===== Background Task: 定時檢查 cookies =====
async def periodic_cookie_check():
    global COOKIE_CHECK_INTERVAL
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    while not client.is_closed():
        try:
            posts = list(get_posts("appledaily.tw", pages=1, cookies=COOKIES_PATH))
            if not posts:
                await channel.send("⚠️ Scheduled check: No posts fetched. Cookies may be expired.")
                add_log("⚠️ Scheduled cookies check failed.")
            else:
                post = posts[0]
                await channel.send(f"✅ Scheduled cookies check success. Latest post_id={post.get('post_id')}")
                add_log(f"✅ Scheduled cookies check success. Got post_id={post.get('post_id')}")
        except Exception as e:
            await channel.send(f"❌ Scheduled cookies check error: {e}")
            add_log(f"❌ Scheduled cookies check error: {e}")

        await asyncio.sleep(COOKIE_CHECK_INTERVAL)

# ===== Helper: 抓取單一粉專 =====
async def fetch_page_posts(channel, page):
    try:
        add_log(f"Checking page: {page}")
        bot_status["last_check"] = f"Checking {page}"

        posts = list(get_posts(page, pages=1, cookies=COOKIES_PATH))

        if not posts:
            add_log(f"⚠️ No posts fetched from {page}. Possible cookies expired.")
            await channel.send(f"⚠️ Warning: No posts fetched from {page}. Cookies may be expired.")
            return

        post = posts[0]
        post_id = post.get("post_id")
        text = post.get("text", "")
        url = post.get("post_url", "")

        if not post_id:
            add_log(f"⚠️ {page} returned no post_id. Cookies may be invalid.")
            return

        add_log(f"Found post {post_id}, preview: {text[:50]}...")

        if not is_post_sent(post_id):
            save_post(post_id)
            msg = f"[{page}] New post:\n{text[:300]}...\nLink: {url}"
            await channel.send(msg)
            bot_status["last_post"] = f"{page} {post_id}"
            add_log(f"Post {post_id} sent to Discord channel {channel.name}")
        else:
            add_log(f"Skipped {page} post {post_id}, already sent")

    except Exception as e:
        add_log(f"❌ ERROR: Failed to fetch {page}: {e}")
        await channel.send(f"❌ ERROR fetching {page}: {e}")

# ===== Discord Events =====
@client.event
async def on_ready():
    add_log(f"Logged in as {client.user}")
    bot_status["logged_in"] = True
    init_db()

    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online and ready!")
        add_log("Test message sent to Discord.")

        # 🚀 啟動時自動檢查 cookies
        try:
            posts = list(get_posts("appledaily.tw", pages=1, cookies=COOKIES_PATH))
            if not posts:
                await channel.send("⚠️ Cookies check failed: No posts fetched. Cookies may be expired.")
                add_log("⚠️ Cookies check failed at startup.")
            else:
                post = posts[0]
                await channel.send(f"✅ Cookies check success at startup. Latest post_id={post.get('post_id')}")
                add_log(f"✅ Cookies check success at startup. Got post_id={post.get('post_id')}")
        except Exception as e:
            await channel.send(f"❌ Cookies check error at startup: {e}")
            add_log(f"❌ Cookies check error at startup: {e}")

    else:
        add_log("❌ Channel not found. Check DISCORD_CHANNEL_ID.")

    # 啟動背景任務
    client.loop.create_task(fetch_facebook_posts())
    client.loop.create_task(periodic_cookie_check())

# ===== Discord Commands =====
@client.event
async def on_message(message):
    global FB_PAGES, COOKIE_CHECK_INTERVAL
    if message.author == client.user:
        return

    content = message.content.strip()

    # 檢查 cookies 狀態
    if content.lower() == "!checkcookies":
        try:
            posts = list(get_posts("appledaily.tw", pages=1, cookies=COOKIES_PATH))
            if not posts:
                await message.channel.send("⚠️ No posts fetched. Cookies may be expired.")
            else:
                post = posts[0]
                await message.channel.send(f"✅ Cookies valid. Latest post_id={post.get('post_id')}")
        except Exception as e:
            await message.channel.send(f"❌ Cookies check error: {e}")

    # 設定 cookies 檢查間隔
    elif content.lower().startswith("!setcheckinterval "):
        parts = content.split(" ", 1)
        if len(parts) == 2 and parts[1].isdigit():
            COOKIE_CHECK_INTERVAL = int(parts[1])
            await message.channel.send(f"⏱️ Cookies check interval updated to {COOKIE_CHECK_INTERVAL} seconds.")
            add_log(f"Cookies check interval updated to {COOKIE_CHECK_INTERVAL} seconds.")
        else:
            await message.channel.send("⚠️ Usage: `!setcheckinterval <seconds>`")

    # 顯示目前設定
    elif content.lower() == "!showconfig":
        pages_list = "\n".join([f"- {p}" for p in FB_PAGES])
        msg = (
            "⚙️ **Current Bot Configuration**\n"
            f"📋 Monitored Pages:\n{pages_list if pages_list else '（空）'}\n\n"
            f"⏱️ Cookies Check Interval: {COOKIE_CHECK_INTERVAL} seconds\n"
            f"🗄️ Database File: {DB_FILE}\n"
            f"🍪 Cookies File: {COOKIES_PATH}\n"
        )
        await message.channel.send(msg)
        add_log("Displayed current configuration.")

    # 立即手動抓取全部
    elif content.lower() == "!fetch":
        await message.channel.send("🔍 Manual fetch started...")
        for page in FB_PAGES:
            await fetch_page_posts(message.channel, page)

    # 立即手動抓取指定粉專
    elif content.lower().startswith("!fetch "):
        parts = content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            await message.channel.send(f"🔍 Manual fetch for {page} started...")
            await fetch_page_posts(message.channel, page)

    # 顯示目前設定的粉專清單
    elif content.lower() == "!listpages":
        pages_list = "\n".join([f"- {p}" for p in FB_PAGES])
        await message.channel.send(f"📋 Current Facebook pages being

# ===== Start Flask keep_alive =====
keep_alive()

# ===== Start Discord Bot =====
client.run(os.getenv("DISCORD_TOKEN"))

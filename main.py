import os
import asyncio
import discord
import sqlite3
from facebook_scraper import get_posts
from keep_alive import keep_alive, bot_status, add_log

intents = discord.Intents.default()
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的頻道 ID
FB_PAGES = ["appledaily.tw", "setnews.tw", "udn.com"]

async def fetch_facebook_posts():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        add_log("❌ Cannot find the Discord channel.")
        return

    add_log("✅ Background task started.")
    await channel.send("🔔 Background task is running and will now test fetch!")

    while not client.is_closed():
        for page in FB_PAGES:
            try:
                add_log(f"Checking page: {page}")
                bot_status["last_check"] = f"Checking {page}"

                # 測試：直接把抓到的原始資料送到 Discord
                for post in get_posts(page, pages=1):
                    await channel.send(f"📡 Raw fetch from {page}:\n{post}")
                    add_log(f"Raw post data from {page}: {post}")
                    break  # 只抓一篇測試
            except Exception as e:
                add_log(f"ERROR: Failed to fetch {page}: {e}")

        add_log("Cycle finished. Sleeping 10 minutes...")
        await asyncio.sleep(600)

@client.event
async def on_ready():
    add_log(f"Logged in as {client.user}")
    bot_status["logged_in"] = True
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online and ready for fetch test!")
        add_log("Test message sent to Discord.")
    else:
        add_log("❌ Channel not found. Check DISCORD_CHANNEL_ID.")
    client.loop.create_task(fetch_facebook_posts())

keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

import os
import asyncio
import discord
from facebook_scraper import get_posts

# ===== Discord Bot 基本設定 =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# 你的 Discord 頻道 ID
DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的頻道 ID
# 你的 FB 粉專名稱或 ID
FB_PAGE = "LARPtimes"  # 範例：蘋果日報粉專

# 用來記錄最後一篇貼文的 ID，避免重複發送
last_post_id = None

async def fetch_facebook_posts():
    global last_post_id
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    while not client.is_closed():
        try:
            for post in get_posts(FB_PAGE, pages=1):
                post_id = post['post_id']
                if post_id != last_post_id:  # 新貼文才發送
                    last_post_id = post_id
                    text = post.get('text', '')[:500]  # 避免太長
                    url = post.get('post_url', '')
                    await channel.send(f"📢 FB 新貼文：\n{text}\n🔗 {url}")
                break  # 只檢查最新一篇
        except Exception as e:
            print(f"抓取失敗: {e}")

        await asyncio.sleep(600)  # 每 600 秒 (10 分鐘) 檢查一次

@client.event
async def on_ready():
    print(f"✅ 已登入 {client.user}")
    client.loop.create_task(fetch_facebook_posts())

client.run(os.getenv("DISCORD_TOKEN"))
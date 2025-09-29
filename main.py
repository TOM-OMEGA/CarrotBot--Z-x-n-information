import os
import discord
import json
from facebook_scraper import get_posts
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DISCORD_CHANNEL_ID = 1047027221811970051  # 換成你的頻道 ID

# ===== Cookies loader =====
def load_cookies():
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # 轉成 {name: value}
        if isinstance(data, list):
            cookies = {item["name"]: item["value"] for item in data if "name" in item and "value" in item}
        elif isinstance(data, dict):
            cookies = data
        else:
            raise ValueError("Invalid cookies.json format")
        return cookies
    except Exception as e:
        print(f"❌ Failed to load cookies.json: {e}")
        return None

@client.event
async def on_ready():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online and ready for debug test!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # 一鍵 debug
    if content.lower() == "!debug":
        cookies = load_cookies()
        if not cookies:
            await message.channel.send("❌ Cannot load cookies.json")
            return

        # 1. 測試 cookies 狀態
        try:
            posts = list(get_posts("appledaily.tw", pages=1, cookies=cookies))
            if not posts:
                await message.channel.send("⚠️ [Cookies] No posts fetched. Cookies may be expired or blocked.")
            else:
                post = posts[0]
                await message.channel.send(f"✅ [Cookies] Valid. Latest post_id={post.get('post_id')}")
        except Exception as e:
            await message.channel.send(f"❌ [Cookies] Error: {e}")

        # 2. 顯示 raw JSON
        try:
            posts = list(get_posts("appledaily.tw", pages=1, cookies=cookies))
            if not posts:
                await message.channel.send("⚠️ [Raw JSON] No data fetched.")
            else:
                post = posts[0]
                raw_text = json.dumps(post, ensure_ascii=False, indent=2)[:1500]
                await message.channel.send(f"📄 [Raw JSON]\n```json\n{raw_text}\n```")
        except Exception as e:
            await message.channel.send(f"❌ [Raw JSON] Error: {e}")

        # 3. 顯示 raw HTML
        try:
            posts = get_posts("appledaily.tw", pages=1, cookies=cookies, options={"raw_html": True})
            first = next(posts, None)
            if not first or "html" not in first:
                await message.channel.send("⚠️ [Raw HTML] No HTML fetched.")
            else:
                html_snippet = first["html"][:1500]
                await message.channel.send(f"📄 [Raw HTML]\n```html\n{html_snippet}\n```")
        except Exception as e:
            await message.channel.send(f"❌ [Raw HTML] Error: {e}")

# ===== 啟動 Flask + Discord Bot =====
keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

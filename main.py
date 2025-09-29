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
        await channel.send("✅ Bot is online and ready for cookie/page/raw/html test!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # 測試 cookies 是否有效（固定測 apple daily）
    if content.lower() == "!checkcookies":
        cookies = load_cookies()
        if not cookies:
            await message.channel.send("❌ Cannot load cookies.json")
            return
        try:
            posts = list(get_posts("appledaily.tw", pages=1, cookies=cookies))
            if not posts:
                await message.channel.send("⚠️ No posts fetched. Cookies may be expired or blocked.")
            else:
                post = posts[0]
                await message.channel.send(f"✅ Cookies valid. Latest post_id={post.get('post_id')}")
        except Exception as e:
            await message.channel.send(f"❌ Cookies check error: {e}")

    # 測試指定粉專
    elif content.lower().startswith("!checkpage "):
        parts = message.content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            cookies = load_cookies()
            if not cookies:
                await message.channel.send("❌ Cannot load cookies.json")
                return
            try:
                posts = list(get_posts(page, pages=1, cookies=cookies))
                if not posts:
                    await message.channel.send(f"⚠️ No posts fetched from {page}. Cookies may be expired or blocked.")
                else:
                    post = posts[0]
                    await message.channel.send(f"✅ {page} OK. Latest post_id={post.get('post_id')}")
            except Exception as e:
                await message.channel.send(f"❌ Error fetching {page}: {e}")

    # 顯示原始 JSON（debug 用）
    elif content.lower().startswith("!rawpage "):
        parts = message.content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            cookies = load_cookies()
            if not cookies:
                await message.channel.send("❌ Cannot load cookies.json")
                return
            try:
                posts = list(get_posts(page, pages=1, cookies=cookies))
                if not posts:
                    await message.channel.send(f"⚠️ No raw data fetched from {page}.")
                else:
                    post = posts[0]
                    raw_text = json.dumps(post, ensure_ascii=False, indent=2)[:1500]
                    await message.channel.send(f"📄 Raw JSON from {page}:\n```json\n{raw_text}\n```")
            except Exception as e:
                await message.channel.send(f"❌ Raw fetch error for {page}: {e}")

    # 顯示原始 HTML（debug 用）
    elif content.lower().startswith("!rawhtml "):
        parts = message.content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            cookies = load_cookies()
            if not cookies:
                await message.channel.send("❌ Cannot load cookies.json")
                return
            try:
                # facebook_scraper 有個參數 options 可以要求回傳原始 HTML
                posts = get_posts(page, pages=1, cookies=cookies, options={"raw_html": True})
                first = next(posts, None)
                if not first or "html" not in first:
                    await message.channel.send(f"⚠️ No raw HTML fetched from {page}.")
                else:
                    html_snippet = first["html"][:1500]  # 只取前 1500 字，避免超過 Discord 限制
                    await message.channel.send(f"📄 Raw HTML from {page}:\n```html\n{html_snippet}\n```")
            except Exception as e:
                await message.channel.send(f"❌ Raw HTML fetch error for {page}: {e}")

# ===== 啟動 Flask + Discord Bot =====
keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

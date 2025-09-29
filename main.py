import os
import discord
import json
import requests
from bs4 import BeautifulSoup
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
        if isinstance(data, list):
            return {item["name"]: item["value"] for item in data if "name" in item and "value" in item}
        return data
    except Exception as e:
        print(f"❌ Failed to load cookies.json: {e}")
        return None

# ===== 抓取 HTML =====
def fetch_bs_html(page_id, cookies):
    url = f"https://www.facebook.com/{page_id}?sk=posts&locale=zh_TW"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.facebook.com/",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Upgrade-Insecure-Requests": "1"
    }
    resp = requests.get(url, headers=headers, cookies=cookies, allow_redirects=True)
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"
    return resp.text, None

# ===== 解析貼文 =====
def parse_posts(html):
    soup = BeautifulSoup(html, "lxml")
    posts = []

    # 1. 嘗試新版 Facebook 結構
    for div in soup.find_all("div", {"data-ad-preview": "message"}):
        text = div.get_text(" ", strip=True)
        if text:
            posts.append(text[:200])

    # 2. 備援：抓 span（避免漏掉）
    if not posts:
        for span in soup.find_all("span"):
            text = span.get_text(" ", strip=True)
            if len(text) > 30:  # 過濾掉太短的
                posts.append(text[:200])

    return posts

@client.event
async def on_ready():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online with improved parse_posts!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # ===== !bsfetch <粉專ID> =====
    if content.lower().startswith("!bsfetch "):
        parts = content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            cookies = load_cookies()
            if not cookies:
                await message.channel.send("❌ Cannot load cookies.json")
                return
            html, error = fetch_bs_html(page, cookies)
            if error:
                await message.channel.send(f"❌ Error fetching {page}: {error}")
            elif not html:
                await message.channel.send(f"⚠️ No HTML fetched from {page}.")
            else:
                posts = parse_posts(html)
                if not posts:
                    await message.channel.send(f"⚠️ No posts parsed from {page}. Maybe blocked or HTML changed.")
                else:
                    preview = "\n".join([f"- {p}" for p in posts[:3]])
                    await message.channel.send(f"✅ Parsed posts from {page}:\n{preview}")

    # ===== !bsraw <粉專ID> =====
    if content.lower().startswith("!bsraw "):
        parts = content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            cookies = load_cookies()
            if not cookies:
                await message.channel.send("❌ Cannot load cookies.json")
                return
            html, error = fetch_bs_html(page, cookies)
            if error:
                await message.channel.send(f"❌ Error fetching {page}: {error}")
            elif not html:
                await message.channel.send(f"⚠️ No HTML fetched from {page}.")
            else:
                snippet = html[:1000]
                await message.channel.send(f"📄 Raw HTML from {page}:\n```html\n{snippet}\n```")

# ===== 啟動 Flask + Discord Bot =====
keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

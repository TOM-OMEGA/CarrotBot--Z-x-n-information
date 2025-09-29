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

# ===== Requests + BeautifulSoup 抓取公開粉專 =====
def fetch_bs_posts(page_id, cookies):
    # 改用 ?sk=posts 強制顯示貼文
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
    soup = BeautifulSoup(resp.text, "lxml")
    posts = []
    for article in soup.find_all("div", {"role": "article"}):
        text = article.get_text(" ", strip=True)
        if text:
            posts.append(text[:200])  # 只取前 200 字
    return posts, None

@client.event
async def on_ready():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online and ready for improved BeautifulSoup test!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    # 新增指令：!bsfetch <粉專ID>
    if content.lower().startswith("!bsfetch "):
        parts = content.split(" ", 1)
        if len(parts) == 2:
            page = parts[1].strip()
            cookies = load_cookies()
            if not cookies:
                await message.channel.send("❌ Cannot load cookies.json")
                return
            posts, error = fetch_bs_posts(page, cookies)
            if error:
                await message.channel.send(f"❌ Error fetching {page}: {error}")
            elif not posts:
                await message.channel.send(f"⚠️ No posts parsed from {page}. Maybe blocked or HTML changed.")
            else:
                preview = "\n".join([f"- {p}" for p in posts[:3]])
                await message.channel.send(f"✅ Parsed posts from {page}:\n{preview}")

# ===== 啟動 Flask + Discord Bot =====
keep_alive()
client.run(os.getenv("DISCORD_TOKEN"))

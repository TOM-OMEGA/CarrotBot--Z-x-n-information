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
DB_FILE = "posts.db"       # SQLite 資料庫檔案

# ===== 初始化資料庫 =====
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def is_post_sent(post_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM posts WHERE post_id = ?", (post_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_post(post_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO posts (post_id) VALUES (?)", (post_id,))
    conn.commit()
    conn.close()

# ===== 抓取 FB 貼文 =====
async def fetch_facebook_posts():
    await client.wait_until_ready()
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    while not client.is_closed():
        try:
            for post in get_posts(FB_PAGE, pages=1):
                post_id = post['post_id']
                if not is_post_sent(post_id):  # 沒發送過才推送
                    save_post(post_id)
                    text = post.get('text', '')[:500]  # 避免太長
                    url = post.get('post_url', '')
                    await channel.send(f"📢 FB 新貼文：\n{text}\n🔗 {url}")
                break  # 只檢查最新一篇
        except Exception as e:
            print(f"抓取失敗: {e}")

        await asyncio.sleep(600)  # 每 10 分鐘檢查一次

@client.event
async def on_ready():
    print(f"✅ 已登入 {client.user}")
    init_db()
    client.loop.create_task(fetch_facebook_posts())

client.run(os.getenv("DISCORD_TOKEN"))

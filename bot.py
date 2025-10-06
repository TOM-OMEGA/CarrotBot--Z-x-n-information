import os
import discord
import requests
import json
from discord.ext import commands

# ---------------------- 基本設定 ----------------------
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://carrotbot-z-x-n-information-wrx7.onrender.com")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------------- 指令：上傳 Cookie ----------------------
@bot.command()
async def fbupload(ctx, *, json_text: str = None):
    """上傳 fb_state.json cookie"""
    if not json_text:
        await ctx.reply("❌ 請附上 cookie JSON 內容！")
        return

    try:
        # 嘗試解析 JSON
        cookie_data = json.loads(json_text)
        res = requests.post(f"{API_URL}/upload", json=cookie_data)
        await ctx.reply(f"伺服器回應：{res.status_code} → {res.text}")
    except Exception as e:
        await ctx.reply(f"❌ 上傳發生錯誤：{e}")


# ---------------------- 指令：啟動爬蟲 ----------------------
@bot.command()
async def fbrun(ctx):
    """啟動 Facebook 爬蟲"""
    await ctx.reply("🚀 正在執行爬蟲...")
    try:
        res = requests.get(f"{API_URL}/run", timeout=10)
        await ctx.reply(f"伺服器回應：{res.status_code} → {res.text}")
    except Exception as e:
        await ctx.reply(f"❌ 執行錯誤：{e}")


# ---------------------- 指令：查詢狀態 ----------------------
@bot.command()
async def fbstatus(ctx):
    """查詢爬蟲狀態與最近貼文"""
    await ctx.reply("📡 正在查詢爬蟲狀態...")
    try:
        res = requests.get(f"{API_URL}/status", timeout=10)
        data = res.json()

        fb_state = "✅" if data.get("fb_state.json") else "❌"
        posts = data.get("recent_posts", [])
        reply_text = f"🗂 fb_state.json：{fb_state}\n📄 貼文數：{len(posts)}"

        if not posts:
            reply_text += "\n❌ 尚無貼文記錄"
            await ctx.reply(reply_text)
            return

        # 顯示最新貼文
        for post in posts:
            content = post.get("content", "(無文字)").strip() or "(無文字)"
            image = post.get("image")

            embed = discord.Embed(
                title="📢 Facebook 最新貼文",
                description=content[:1500],
                color=0x00AAFF
            )
            embed.set_footer(text=f"🕓 {post.get('timestamp')}")
            if image:
                embed.set_image(url=image)

            await ctx.send(embed=embed)

    except Exception as e:
        await ctx.reply(f"❌ 無法查詢狀態：{e}")


# ---------------------- 啟動 ----------------------
@bot.event
async def on_ready():
    print(f"🤖 已登入 Discord：{bot.user}")
    print(f"🌐 API_URL：{API_URL}")

bot.run(DISCORD_BOT_TOKEN)

import discord
from discord.ext import commands
import requests
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = os.getenv("SCRAPER_API_URL")

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot 已啟動：{client.user}")

# 📦 !fbrefresh：更新 Facebook 登入狀態
@client.command()
async def fbrefresh(ctx):
    await ctx.send("🔄 正在更新 Facebook 登入狀態...")
    try:
        r = requests.get(f"{API_URL}/refresh-login", timeout=30)
        await ctx.send(r.text)
    except Exception as e:
        await ctx.send(f"⚠️ 錯誤：{str(e)}")

# 📦 !fbstatus：查詢爬蟲系統健康狀態
@client.command()
async def fbstatus(ctx):
    await ctx.send("📡 正在查詢爬蟲狀態...")
    try:
        r = requests.get(f"{API_URL}/status", timeout=15)
        data = r.json()
        if "error" in data:
            await ctx.send(f"❌ 錯誤：{data['error']}")
        else:
            msg = (
                f"🗂 fb_state.json：{data['fb_state_exists']}\n"
                f"🔐 FB_EMAIL：{data['env_FB_EMAIL']}\n"
                f"🔐 FB_PASSWORD：{data['env_FB_PASSWORD']}\n"
                f"📣 Webhook：{data['env_DISCORD_WEBHOOK_URL']}\n"
                f"📝 最近貼文：\n" +
                "\n".join([f"- {p['created_at'][:19]} → {p['content'][:50]}" for p in data["recent_posts"]])
            )
            await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"⚠️ 錯誤：{str(e)}")

# 📦 !fbrun：執行爬蟲並推送貼文
@client.command()
async def fbrun(ctx):
    await ctx.send("🚀 正在執行爬蟲...")
    try:
        r = requests.get(f"{API_URL}/run", timeout=60)
        await ctx.send(r.text)
    except Exception as e:
        await ctx.send(f"⚠️ 錯誤：{str(e)}")

# 📦 !debuglogin：擷取 Facebook 登入畫面
@client.command()
async def debuglogin(ctx):
    await ctx.send("🧪 擷取 Facebook 登入畫面中...")
    try:
        r = requests.get(f"{API_URL}/debug-login", timeout=30)
        data = r.json()
        if "image_base64" in data:
            preview = data["image_base64"][:500] + "..."
            await ctx.send("📷 登入畫面擷取成功（base64 預覽）：")
            await ctx.send(f"```{preview}```")
            await ctx.send("🔧 可用 [base64-to-image](https://codebeautify.org/base64-to-image-converter) 還原圖片")
        else:
            await ctx.send(f"❌ 登入畫面錯誤：{data.get('error', '未知錯誤')}")
    except Exception as e:
        await ctx.send(f"⚠️ 錯誤：{str(e)}")

# 📦 !fbcheck：一鍵診斷系統狀態與登入畫面
@client.command()
async def fbcheck(ctx):
    await ctx.send("🧪 正在執行系統診斷...")
    try:
        r1 = requests.get(f"{API_URL}/status", timeout=15)
        data = r1.json()
        if "error" in data:
            await ctx.send(f"❌ 狀態錯誤：{data['error']}")
        else:
            msg = (
                f"🗂 fb_state.json：{data['fb_state_exists']}\n"
                f"🔐 FB_EMAIL：{data['env_FB_EMAIL']}\n"
                f"🔐 FB_PASSWORD：{data['env_FB_PASSWORD']}\n"
                f"📣 Webhook：{data['env_DISCORD_WEBHOOK_URL']}\n"
                f"📝 最近貼文：\n" +
                "\n".join([f"- {p['created_at'][:19]} → {p['content'][:50]}" for p in data["recent_posts"]])
            )
            await ctx.send(msg)

        r2 = requests.get(f"{API_URL}/debug-login", timeout=30)
        data2 = r2.json()
        if "image_base64" in data2:
            preview = data2["image_base64"][:500] + "..."
            await ctx.send("📷 登入畫面擷取成功（base64 預覽）：")
            await ctx.send(f"```{preview}```")
            await ctx.send("🔧 可用 [base64-to-image](https://codebeautify.org/base64-to-image-converter) 還原圖片")
        else:
            await ctx.send(f"❌ 登入畫面錯誤：{data2.get('error', '未知錯誤')}")
    except Exception as e:
        await ctx.send(f"⚠️ 系統診斷失敗：{str(e)}")

# 📦 !fbhelp：顯示所有指令與用途說明
@client.command()
async def fbhelp(ctx):
    help_msg = (
        "**🧭 FB爬蟲助手指令總覽**\n"
        "`!fbrefresh` → 更新 Facebook 登入狀態\n"
        "`!fbstatus` → 查詢爬蟲系統健康狀態\n"
        "`!fbrun` → 執行爬蟲並推送貼文\n"
        "`!debuglogin` → 擷取 Facebook 登入畫面\n"
        "`!fbcheck` → 一鍵診斷系統狀態與登入畫面\n"
        "`!fbhelp` → 顯示所有指令與用途說明"
    )
    await ctx.send(help_msg)

# ✅ 啟動 Bot
client.run(TOKEN)

import discord
from discord.ext import commands
from discord import app_commands
import requests
import os

# 使用 Render 的環境變數
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = os.getenv("SCRAPER_API_URL")

# 啟用 intents
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)

@client.event
async def on_ready():
    await client.tree.sync()
    print(f"✅ Bot 已啟動：{client.user}")

# 📦 更新 Facebook 登入狀態
@client.tree.command(name="fbrefresh", description="更新 Facebook 登入狀態")
async def fbrefresh(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 正在更新 Facebook 登入狀態...")
    try:
        r = requests.get(f"{API_URL}/refresh-login", timeout=30)
        await interaction.followup.send(r.text)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 錯誤：{str(e)}")

# 📦 查詢爬蟲系統健康狀態
@client.tree.command(name="fbstatus", description="查詢爬蟲系統健康狀態")
async def fbstatus(interaction: discord.Interaction):
    await interaction.response.send_message("📡 正在查詢爬蟲狀態...")
    try:
        r = requests.get(f"{API_URL}/status", timeout=15)
        data = r.json()
        if "error" in data:
            await interaction.followup.send(f"❌ 錯誤：{data['error']}")
        else:
            msg = (
                f"🗂 fb_state.json：{data['fb_state_exists']}\n"
                f"🔐 FB_EMAIL：{data['env_FB_EMAIL']}\n"
                f"🔐 FB_PASSWORD：{data['env_FB_PASSWORD']}\n"
                f"📣 Webhook：{data['env_DISCORD_WEBHOOK_URL']}\n"
                f"📝 最近貼文：\n" +
                "\n".join([f"- {p['created_at'][:19]} → {p['content'][:50]}" for p in data["recent_posts"]])
            )
            await interaction.followup.send(msg)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 錯誤：{str(e)}")

# 📦 執行爬蟲並推送貼文
@client.tree.command(name="fbrun", description="執行爬蟲並推送貼文")
async def fbrun(interaction: discord.Interaction):
    await interaction.response.send_message("🚀 正在執行爬蟲...")
    try:
        r = requests.get(f"{API_URL}/run", timeout=60)
        await interaction.followup.send(r.text)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 錯誤：{str(e)}")

# 📦 擷取 Facebook 登入畫面
@client.tree.command(name="debuglogin", description="擷取 Facebook 登入畫面")
async def debuglogin(interaction: discord.Interaction):
    await interaction.response.send_message("🧪 擷取 Facebook 登入畫面中...")
    try:
        r = requests.get(f"{API_URL}/debug-login", timeout=30)
        data = r.json()
        if "image_base64" in data:
            preview = data["image_base64"][:500] + "..."
            await interaction.followup.send("📷 登入畫面擷取成功（base64 預覽）：")
            await interaction.followup.send(f"```{preview}```")
            await interaction.followup.send("🔧 可用 [base64-to-image](https://codebeautify.org/base64-to-image-converter) 還原圖片")
        else:
            await interaction.followup.send(f"❌ 登入畫面錯誤：{data.get('error', '未知錯誤')}")
    except Exception as e:
        await interaction.followup.send(f"⚠️ 錯誤：{str(e)}")

# 📦 一鍵診斷系統狀態與登入畫面
@client.tree.command(name="fbcheck", description="一鍵診斷爬蟲系統狀態與登入畫面")
async def fbcheck(interaction: discord.Interaction):
    await interaction.response.send_message("🧪 正在執行系統診斷...")
    try:
        r1 = requests.get(f"{API_URL}/status", timeout=15)
        data = r1.json()
        if "error" in data:
            await interaction.followup.send(f"❌ 狀態錯誤：{data['error']}")
        else:
            msg = (
                f"🗂 fb_state.json：{data['fb_state_exists']}\n"
                f"🔐 FB_EMAIL：{data['env_FB_EMAIL']}\n"
                f"🔐 FB_PASSWORD：{data['env_FB_PASSWORD']}\n"
                f"📣 Webhook：{data['env_DISCORD_WEBHOOK_URL']}\n"
                f"📝 最近貼文：\n" +
                "\n".join([f"- {p['created_at'][:19]} → {p['content'][:50]}" for p in data["recent_posts"]])
            )
            await interaction.followup.send(msg)

        r2 = requests.get(f"{API_URL}/debug-login", timeout=30)
        data2 = r2.json()
        if "image_base64" in data2:
            preview = data2["image_base64"][:500] + "..."
            await interaction.followup.send("📷 登入畫面擷取成功（base64 預覽）：")
            await interaction.followup.send(f"```{preview}```")
            await interaction.followup.send("🔧 可用 [base64-to-image](https://codebeautify.org/base64-to-image-converter) 還原圖片")
        else:
            await interaction.followup.send(f"❌ 登入畫面錯誤：{data2.get('error', '未知錯誤')}")
    except Exception as e:
        await interaction.followup.send(f"⚠️ 系統診斷失敗：{str(e)}")

# 📦 顯示所有指令與用途說明
@client.tree.command(name="fbhelp", description="顯示所有指令與用途說明")
async def fbhelp(interaction: discord.Interaction):
    help_msg = (
        "**🧭 FB爬蟲助手指令總覽**\n"
        "`/fbrefresh` → 更新 Facebook 登入狀態\n"
        "`/fbstatus` → 查詢爬蟲系統健康狀態\n"
        "`/fbrun` → 執行爬蟲並推送貼文\n"
        "`/debuglogin` → 擷取 Facebook 登入畫面\n"
        "`/fbcheck` → 一鍵診斷系統狀態與登入畫面\n"
        "`/fbhelp` → 顯示所有指令與用途說明"
    )
    await interaction.response.send_message(help_msg)

# ✅ 啟動 Bot
client.run(TOKEN)

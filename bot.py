import discord
from discord.ext import commands
import requests
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = "https://carrotbot-z-x-n-information.onrender.com".rstrip("/")

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
        # 呼叫 /status
        r1 = requests.get(f"{API_URL}/status", timeout=15)
        try:
            data = r1.json()
        except Exception as e:
            await ctx.send(f"❌ 無法解析 /status 回應：{r1.text[:200]}")
            return

        # 分析 /status 回應
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

        # 呼叫 /debug-login
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

@client.command()
async def fbraw(ctx):
    await ctx.send("📡 正在擷取 /status 原始回應...")
    try:
        r = requests.get(f"{API_URL}/status", timeout=15)
        await ctx.send(f"```{r.text[:1500]}```")
    except Exception as e:
        await ctx.send(f"⚠️ 錯誤：{str(e)}")

@client.command()
async def fbview(ctx):
    if os.path.exists("login_error.png"):
        await ctx.send(file=discord.File("login_error.png"))
    else:
        await ctx.send("⚠️ 尚未擷取登入錯誤畫面，請先執行 login_once.py 或使用 !debuglogin")

@client.command()
async def fbupload(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ 請附加 fb_state.json 檔案")
        return

    attachment = ctx.message.attachments[0]
    if attachment.filename != "fb_state.json":
        await ctx.send("⚠️ 檔名必須為 fb_state.json")
        return

    try:
        file_bytes = await attachment.read()
        r = requests.post(f"{API_URL}/upload-cookie", files={"file": ("fb_state.json", file_bytes)})
        await ctx.send(r.text)
        await ctx.send(f"伺服器回應：{r.status_code} → {r.text}")
    except Exception as e:
        await ctx.send(f"❌ 上傳失敗：{str(e)}")

@client.command()
async def fbroute(ctx):
    try:
        r = requests.get(f"{API_URL}/routes", timeout=10)
        await ctx.send(f"📚 路由列表：\n```{r.text}```")
    except Exception as e:
        await ctx.send(f"⚠️ 無法取得路由：{str(e)}")

@client.command()
async def fbclear(ctx):
    try:
        r = requests.post(f"{API_URL}/clear-cookie", timeout=10)
        await ctx.send(f"🧹 清除結果：{r.status_code} → {r.text}")
    except Exception as e:
        await ctx.send(f"⚠️ 清除失敗：{str(e)}")

@client.command()
async def fbpanel(ctx):
    await ctx.send("📊 正在載入系統面板...")
    try:
        r1 = requests.get(f"{API_URL}/status", timeout=15)
        data = r1.json()
        msg = (
            f"🗂 fb_state.json：{data['fb_state_exists']}\n"
            f"🔐 FB_EMAIL：{data['env_FB_EMAIL']}\n"
            f"🔐 FB_PASSWORD：{data['env_FB_PASSWORD']}\n"
            f"📣 Webhook：{data['env_DISCORD_WEBHOOK_URL']}\n"
            f"📝 最近貼文：\n" +
            "\n".join([f"- {p['created_at'][:19]} → {p['content'][:50]}" for p in data.get("recent_posts", [])])
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
        await ctx.send(f"⚠️ 面板載入失敗：{str(e)}")
        
# 📦 !fbhelp：顯示所有指令與用途說明
@client.command()
async def fbhelp(ctx):
    help_msg = (
        "**🧭 FB爬蟲助手指令總覽**\n\n"
        "**📡 系統狀態與診斷**\n"
        "`!fbstatus` → 查詢爬蟲系統健康狀態\n"
        "`!fbcheck` → 一鍵診斷登入狀態與登入畫面\n"
        "`!fbraw` → 顯示 /status 原始回應內容\n"
        "`!fbroute` → 顯示 Flask 所有 API 路由\n"
        "`!fbpanel` → 顯示系統面板（狀態 + 登入畫面）\n\n"
        "**🔐 登入與 Cookie 管理**\n"
        "`!fbupload` → 上傳登入 cookie（fb_state.json）\n"
        "`!fbclear` → 清除伺服器上的 cookie\n"
        "`!debuglogin` → 擷取 Facebook 登入畫面（base64）\n"
        "`!fbview` → 回傳登入錯誤畫面 login_error.png\n\n"
        "**🚀 執行爬蟲與推送貼文**\n"
        "`!fbrun` → 執行爬蟲並推送貼文\n"
        "`!fbrefresh` → 更新 Facebook 登入狀態\n\n"
        "**📖 說明與幫助**\n"
        "`!fbhelp` → 顯示所有指令與用途說明"
    )
    await ctx.send(help_msg)

# ✅ 啟動 Bot
client.run(TOKEN)

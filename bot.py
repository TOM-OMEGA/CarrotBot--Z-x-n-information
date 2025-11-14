import discord
from discord.ext import commands, tasks
from keep_alive import keep_alive
from PIL import Image, ImageDraw, ImageFont
from pypinyin import pinyin, Style
import io, os

# ===== Bot 基本設定 =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== 字體路徑 =====
FONT_PATH_ROCK = "fonts/elffont-rock.otf"
FONT_PATH_FERN = "fonts/elffont-fern.otf"

# ===== 文字轉注音（自動支援全部漢字）=====
def chinese_to_zhuyin(text: str) -> str:
    result = pinyin(text, style=Style.BOPOMOFO, strict=False)
    bopomofo = "".join([item[0] for item in result])
    return bopomofo

# ===== 生成精靈文圖片 =====
def make_elf_image(text: str, font_path: str):
    bopomo_text = chinese_to_zhuyin(text)

    font_size = 110
    font = ImageFont.truetype(font_path, font_size)

    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    w, h = d.textsize(bopomo_text, font=font)

    img = Image.new("RGBA", (w + 80, h + 80), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), bopomo_text, fill=(0, 0, 0, 255), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ===== Bot 狀態 =====
@bot.event
async def on_ready():
    print(f"登入成功：{bot.user}")
    keep_alive_ping.start()

# ===== 指令：岩 =====
@bot.command()
async def 精靈文岩(ctx, *, text: str):
    img_bytes = make_elf_image(text, FONT_PATH_ROCK)
    await ctx.send(file=discord.File(img_bytes, "elf_rock.png"))

# ===== 指令：蕨 =====
@bot.command()
async def 精靈文蕨(ctx, *, text: str):
    img_bytes = make_elf_image(text, FONT_PATH_FERN)
    await ctx.send(file=discord.File(img_bytes, "elf_fern.png"))

# ===== Render 保活 =====
@tasks.loop(minutes=5)
async def keep_alive_ping():
    print("[KeepAlive] Ping...")

keep_alive()

# ===== 啟動 Bot =====
bot.run(os.getenv("DISCORD_TOKEN"))

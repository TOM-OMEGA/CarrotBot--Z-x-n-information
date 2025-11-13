import sys
# 🚫 避免 Discord.py 語音模組 crash
sys.modules['discord.player'] = None
sys.modules['discord.voice_client'] = None

import discord
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont
import io, os, time
from keep_alive import keep_alive

# ====== Bot 基本設定 ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== 字體路徑 ======
FONT_PATHS = {
    "岩": "fonts/elffont-rock.otf",
    "蕨": "fonts/elffont-fern.otf",
}

# ====== 簡易漢字→注音字典 ======
zhuyin_dict = {
    "我": "ㄨㄛˇ", "你": "ㄋㄧˇ", "他": "ㄊㄚ", "是": "ㄕˋ",
    "精": "ㄐㄧㄥ", "靈": "ㄌㄧㄥˊ", "文": "ㄨㄣˊ",
    "好": "ㄏㄠˇ", "的": "ㄉㄜ˙", "嗎": "ㄇㄚ˙",
    "在": "ㄗㄞˋ", "玩": "ㄨㄢˊ", "嗎": "ㄇㄚ˙",
}

# ====== 文字轉注音 ======
def chinese_to_zhuyin(text):
    return "".join(zhuyin_dict.get(ch, ch) for ch in text)

# ====== 生成精靈文字圖片 ======
def generate_elf_image(text: str, style: str):
    font_path = FONT_PATHS.get(style)
    if not font_path or not os.path.exists(font_path):
        raise FileNotFoundError(f"找不到字體檔案：{font_path}")

    zhuyin_text = chinese_to_zhuyin(text)

    font_size = 100
    font = ImageFont.truetype(font_path, font_size)
    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    text_width, text_height = draw.textsize(zhuyin_text, font=font)

    img = Image.new("RGBA", (text_width + 80, text_height + 80), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), zhuyin_text, font=font, fill=(0, 0, 0, 255))

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

# ====== Bot 指令 ======
@bot.event
async def on_ready():
    print(f"✅ 已登入：{bot.user}")
    keep_alive_ping.start()

@bot.command()
async def 精靈文岩(ctx, *, text: str):
    try:
        image_bytes = generate_elf_image(text, "岩")
        file = discord.File(image_bytes, filename="elf_rock.png")
        await ctx.send(f"🌋 精靈文（岩）", file=file)
    except Exception as e:
        await ctx.send(f"發生錯誤：{e}")

@bot.command()
async def 精靈文蕨(ctx, *, text: str):
    try:
        image_bytes = generate_elf_image(text, "蕨")
        file = discord.File(image_bytes, filename="elf_fern.png")
        await ctx.send(f"🌿 精靈文（蕨）", file=file)
    except Exception as e:
        await ctx.send(f"發生錯誤：{e}")

# ====== 防止離線 Ping ======
@tasks.loop(minutes=5)
async def keep_alive_ping():
    print(f"[{time.strftime('%H:%M:%S')}] ⏳ Keep-alive ping sent.")

# ====== 啟動 Flask 保活伺服器 ======
keep_alive()

# ====== 啟動機器人 ======
bot.run("你的 Discord Bot Token")

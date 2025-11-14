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
def make_elf_image(text: str, font_path: str, max_width: int = 1000, padding: int = 40):
    bopomo_text = chinese_to_zhuyin(text)

    # 初始字體大小
    font_size = 110
    font = ImageFont.truetype(font_path, font_size)

    # 換行處理
    def wrap_text(text, draw, font, max_width):
        lines = []
        words = list(text)
        line = ""
        for char in words:
            test_line = line + char
            w, _ = draw.textsize(test_line, font=font)
            if w + 2 * padding > max_width:
                if line:
                    lines.append(line)
                line = char
            else:
                line = test_line
        if line:
            lines.append(line)
        return lines

    # 計算文字尺寸，若超過 max_width，自動縮小字體
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    lines = wrap_text(bopomo_text, draw, font, max_width)
    w = max(draw.textsize(line, font=font)[0] for line in lines)
    h = sum(draw.textsize(line, font=font)[1] for line in lines) + (len(lines)-1) * 10

    while w + 2*padding > max_width and font_size > 20:
        font_size -= 5
        font = ImageFont.truetype(font_path, font_size)
        lines = wrap_text(bopomo_text, draw, font, max_width)
        w = max(draw.textsize(line, font=font)[0] for line in lines)
        h = sum(draw.textsize(line, font=font)[1] for line in lines) + (len(lines)-1) * 10

    # 背景與文字顏色
    background_color = (245, 245, 245, 255)  # 淡灰白
    text_color = (60, 60, 60, 255)           # 深灰
    shadow_color = (150, 150, 150, 255)      # 陰影

    img = Image.new("RGBA", (w + 2*padding, h + 2*padding), background_color)
    draw = ImageDraw.Draw(img)

    # 畫文字（附陰影）
    shadow_offset = 2
    y = padding
    for line in lines:
        draw.text((padding + shadow_offset, y + shadow_offset), line, fill=shadow_color, font=font)
        draw.text((padding, y), line, fill=text_color, font=font)
        y += draw.textsize(line, font=font)[1] + 10  # 行間距 10px

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

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
FONT_PATH_NUM_EN = "fonts/NotoSans-Regular.ttf"  # 英文和數字字型

# ===== 文字轉注音 =====
def chinese_to_zhuyin(text: str) -> str:
    result = pinyin(text, style=Style.BOPOMOFO, strict=False)
    return "".join([item[0] for item in result])

# ===== 生成精靈文圖片（自動縮放字型 + 自動換行 + 文字居中） =====
def make_elf_image(text: str, font_path: str):
    bopomo_text = chinese_to_zhuyin(text)

    max_width = 1200
    base_font_size = 110
    min_font_size = 40

    # 嘗試最大字型
    font_size = base_font_size
    while font_size >= min_font_size:
        font_elf = ImageFont.truetype(font_path, font_size)
        font_num_en = ImageFont.truetype(FONT_PATH_NUM_EN, font_size)

        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)

        # 使用新的換行函數
        def wrap_text(draw, text, font_elf, font_num, max_width):
            lines = []
            line = ""
            for char in text:
                test_line = line + char
                w = 0
                for c in test_line:
                    font = font_num if c.isascii() else font_elf
                    bbox = draw.textbbox((0,0), c, font=font)
                    w += bbox[2]-bbox[0]
                if w <= max_width:
                    line = test_line
                else:
                    if line:
                        lines.append(line)
                    line = char
            if line:
                lines.append(line)
            return lines

        lines = wrap_text(draw, bopomo_text, font_elf, font_num_en, max_width)

        # 計算整體高度
        line_height = font_size + 20
        img_height = line_height * len(lines) + 80
        img_width = max_width + 80

        # 如果總寬或總高過大，縮小字型再試
        if len(lines) * line_height <= img_height:
            break
        font_size -= 5

    img = Image.new("RGBA", (img_width, img_height), (245, 245, 245, 255))  # 淡背景
    draw = ImageDraw.Draw(img)

    # 畫字並居中
    y = 40
    for line in lines:
        # 計算該行寬度
        line_width = 0
        for char in line:
            font = font_num_en if char.isascii() else font_elf
            bbox = draw.textbbox((0,0), char, font=font)
            line_width += bbox[2]-bbox[0]
        x = (img_width - line_width) // 2  # 居中起始x

        for char in line:
            font = font_num_en if char.isascii() else font_elf
            draw.text((x, y), char, font=font, fill=(50,50,50,255))
            bbox = draw.textbbox((0,0), char, font=font)
            x += bbox[2]-bbox[0]
        y += line_height

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ===== Bot 狀態 =====
@bot.event
async def on_ready():
    print(f"登入成功：{bot.user}")
    keep_alive_ping.start()

# ===== 指令 =====
@bot.command()
async def 精靈文岩(ctx, *, text: str):
    img_bytes = make_elf_image(text, FONT_PATH_ROCK)
    await ctx.send(file=discord.File(img_bytes, "elf_rock.png"))

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

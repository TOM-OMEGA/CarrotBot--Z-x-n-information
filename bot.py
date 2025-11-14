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

# ===== 生成精靈文圖片（自動縮放 + 換行 + 居中） =====
def make_elf_image(text: str, font_path: str):
    bopomo_text = chinese_to_zhuyin(text)

    max_width = 1200
    base_font_size = 110
    min_font_size = 40
    padding = 40
    line_spacing = 20

    # 嘗試最大字型
    font_size = base_font_size
    font_elf = ImageFont.truetype(font_path, font_size)
    font_num_en = ImageFont.truetype(FONT_PATH_NUM_EN, font_size)

    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)

    # 先測量單行總寬度
    total_width = 0
    for char in bopomo_text:
        if char.isascii():
            bbox = draw.textbbox((0,0), char, font=font_num_en)
        else:
            bbox = draw.textbbox((0,0), char, font=font_elf)
        total_width += bbox[2]-bbox[0]

    # 自動縮放字型
    if total_width > max_width:
        scale = max_width / total_width
        font_size = max(int(font_size * scale), min_font_size)
        font_elf = ImageFont.truetype(font_path, font_size)
        font_num_en = ImageFont.truetype(FONT_PATH_NUM_EN, font_size)

    # 換行處理
    lines = []
    line = ""
    draw = ImageDraw.Draw(Image.new("RGBA", (1,1)))
    for char in bopomo_text:
        test_line = line + char
        w = 0
        for c in test_line:
            if c.isascii():
                bbox = draw.textbbox((0,0), c, font=font_num_en)
            else:
                bbox = draw.textbbox((0,0), c, font=font_elf)
            w += bbox[2]-bbox[0]
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = char
    if line:
        lines.append(line)

    # 計算每行高度
    line_heights = []
    for line in lines:
        h = 0
        for c in line:
            if c.isascii():
                bbox = draw.textbbox((0,0), c, font=font_num_en)
            else:
                bbox = draw.textbbox((0,0), c, font=font_elf)
            h = max(h, bbox[3]-bbox[1])
        line_heights.append(h)

    # 計算圖片尺寸
    img_width = max([sum(draw.textbbox((0,0), c, font=font_num_en if c.isascii() else font_elf)[2]-draw.textbbox((0,0), c, font=font_num_en if c.isascii() else font_elf)[0] for c in line) for line in lines]) + padding*2
    img_width = min(img_width, max_width + padding*2)
    img_height = sum(line_heights) + line_spacing*(len(lines)-1) + padding*2

    img = Image.new("RGBA", (img_width, img_height), (245,245,245,255))
    draw = ImageDraw.Draw(img)

    # 畫文字
    y = padding
    for idx, line in enumerate(lines):
        # 計算行寬
        line_width = 0
        for c in line:
            bbox = draw.textbbox((0,0), c, font=font_num_en if c.isascii() else font_elf)
            line_width += bbox[2]-bbox[0]
        x = (img_width - line_width)//2
        for c in line:
            draw.text((x, y), c, font=font_num_en if c.isascii() else font_elf, fill=(50,50,50,255))
            bbox = draw.textbbox((0,0), c, font=font_num_en if c.isascii() else font_elf)
            x += bbox[2]-bbox[0]
        y += line_heights[idx] + line_spacing

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

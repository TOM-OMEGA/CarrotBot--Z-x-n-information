import hikari
import lightbulb
from PIL import Image, ImageDraw, ImageFont
import os
from dotenv import load_dotenv
from keepalive import keep_alive

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Discord Bot
bot = lightbulb.BotApp(
    token=TOKEN,
    prefix="!",
    intents=hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT
)

# 精靈文字產圖功能
def generate_elf_image(text: str, font_path: str = "fonts/elffont-fern.otf"):
    font_size = 64
    font = ImageFont.truetype(font_path, font_size)
    # 計算文字尺寸
    width, height = font.getsize_multiline(text)
    image = Image.new("RGBA", (width+20, height+20), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.text((10,10), text, font=font, fill=(0,0,0,255))
    return image

# Bot 指令
@bot.command
@lightbulb.command("elf", "Convert text to elf font image")
@lightbulb.implements(lightbulb.PrefixCommand)
async def elf(ctx: lightbulb.Context):
    content = ctx.message.content
    # 取得命令後文字
    parts = content.split(" ", 1)
    if len(parts) < 2:
        await ctx.respond("請輸入要轉換的文字！")
        return
    text = parts[1]
    img = generate_elf_image(text)
    img_path = "temp.png"
    img.save(img_path)
    await ctx.respond(file=disnake.File(img_path))

# 保活
keep_alive()

# 啟動 Bot
bot.run()

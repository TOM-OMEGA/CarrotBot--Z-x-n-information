import nextcord
from nextcord.ext import commands, tasks
from keep_alive import keep_alive
from PIL import Image, ImageDraw, ImageFont
from pypinyin import pinyin, Style
import io, os


intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

FONT_PATH_ROCK = "fonts/elffont-rock.otf"
FONT_PATH_FERN = "fonts/elffont-fern.otf"


def chinese_to_zhuyin(text: str) -> str:
    result = pinyin(text, style=Style.BOPOMOFO, strict=False)
    return "".join([item[0] for item in result])


def make_elf_image(text: str, font_path: str):
    bopomo = chinese_to_zhuyin(text)
    font = ImageFont.truetype(font_path, 110)

    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    w, h = d.textsize(bopomo, font=font)

    img = Image.new("RGBA", (w + 80, h + 80), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), bopomo, fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    keep_alive_ping.start()


@tasks.loop(minutes=5)
async def keep_alive_ping():
    print("Render keep-alive ping...")


@bot.command()
async def 精靈文岩(ctx, *, text: str):
    img = make_elf_image(text, FONT_PATH_ROCK)
    await ctx.send(file=nextcord.File(img, "elf_rock.png"))


@bot.command()
async def 精靈文蕨(ctx, *, text: str):
    img = make_elf_image(text, FONT_PATH_FERN)
    await ctx.send(file=nextcord.File(img, "elf_fern.png"))


keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))

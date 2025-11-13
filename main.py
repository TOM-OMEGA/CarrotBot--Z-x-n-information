import discord
import os
from discord.ext import commands
from discord import option

from pypinyin import pinyin, Style
from PIL import Image, ImageDraw, ImageFont
import io 
from flask import Flask
from threading import Thread

# --- 全域設定 ---
# 載入兩種風格的字型路徑
FONT_ROCK_PATH = 'fonts/elffont-rock.otf'
FONT_FERN_PATH = 'fonts/elffont-fern.otf'

# 機器人 Token (必須在 Render 環境變數中設定 DISCORD_TOKEN)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    print("!!! 警告：DISCORD_TOKEN 環境變數未設定。")

# --- Discord Bot 設定 ---
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"機器人 {bot.user} 已登入並在執行緒中運行！")

@bot.slash_command(name="elf", description="將中文訊息轉換為精靈注音圖片")
# 參數 1: 要轉換的文字
@option("text", str, description="請輸入要轉換的中文", required=True)
# 參數 2: 風格選擇
@option(
    "style",
    str,
    description="選擇精靈文字的風格",
    choices=["rock", "fern"], 
    default="rock" # 預設使用 rock 風格
)
async def elf_converter(ctx: discord.ApplicationContext, text: str, style: str): 
    
    # 立即回應，避免超時
    await ctx.defer()
    
    # 根據 style 參數決定要載入哪一個字型檔
    if style == "rock":
        current_font_path = FONT_ROCK_PATH
    elif style == "fern":
        current_font_path = FONT_FERN_PATH
    else:
        current_font_path = FONT_ROCK_PATH # 預設

    try:
        # 步驟 1: 中文轉注音
        bpmf_list = pinyin(text, style=Style.BOPOMOFO)
        bpmf_text = " ".join([p[0] for p in bpmf_list])
        
        if not bpmf_text.strip():
             await ctx.respond("轉換失敗，請確認輸入的是中文。", ephemeral=True)
             return

        # 步驟 2: 載入字型與設定
        font_size = 40
        padding = 20
        # 載入動態選擇的字型路徑
        font = ImageFont.truetype(current_font_path, size=font_size) 

        # 步驟 3: 計算圖片大小
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), bpmf_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width = text_width + (padding * 2)
        img_height = text_height + (padding * 2)

        # 步驟 4: 建立真實圖片 (透明背景)
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # 步驟 5: 繪製文字 (白色)
        d.text(
            (padding, padding - bbox[1]),
            bpmf_text,
            font=font,
            fill="#FFFFFF"
        )

        # 步驟 6: 儲存到記憶體並發送
        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            await ctx.respond(
                f"你說的「{text}」 ({style} 風格) 精靈語是：",
                file=discord.File(fp=image_binary, filename='elf.png')
            )

    except Exception as e:
        print(f"處理 /elf 指令時發生錯誤: {e}")
        # 如果字型載入失敗，這裡會回報錯誤
        await ctx.respond(f"糟糕，轉換時發生了錯誤！可能是字型路徑錯誤或 Render 環境問題。\n錯誤訊息：`{e}`")


# --- Flask 網頁伺服器設定 (Render Web Service 免費版 必需) ---
app = Flask(__name__)

# 建立一個簡單的首頁給 Render 健康檢查使用
@app.route('/')
def home():
    return "Elf Discord Bot is active (Web Service Workaround)."

# 負責在背景啟動 Discord Bot 的函式
def run_bot():
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("!!! 錯誤：DISCORD_TOKEN 未設定。Bot 未啟動。")

# --- 主執行區塊 ---
# 這是 Render 的 Gunicorn 啟動時會執行的區域
if __name__ == '__main__':
    # 在背景執行緒啟動 Discord Bot
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # 由於 Render 的 Start Command 會使用 gunicorn main:app 來啟動 Flask 應用，
    # 這裡的 app.run() 其實不會被執行，但保留結構以供測試。
    # 實際部署時，Flask 應用會在主執行緒中被 Gunicorn 啟動並監聽通訊埠。
    print("程式正在等待 Render 的 Gunicorn 啟動指令來運行 Flask 伺服器...")

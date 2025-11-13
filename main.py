import discord
import os
from discord.ext import commands
from discord import option

from pypinyin import pinyin, Style
from PIL import Image, ImageDraw, ImageFont
import io 
from flask import Flask
from threading import Thread # 引入執行緒模組

# --- 設定 ---
FONT_PATH = 'Elffont.ttf'
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- 1. Discord Bot 設定 (與之前相同) ---
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"機器人 {bot.user} 已登入並在執行緒中運行！")

@bot.slash_command(name="elf", description="將中文訊息轉換為精靈注音圖片")
@option("text", str, description="請輸入要轉換的中文", required=True)
async def elf_converter(ctx: discord.ApplicationContext, text: str):
    await ctx.defer()
    
    # 您的圖片生成邏輯 (與之前版本相同)
    try:
        bpmf_list = pinyin(text, style=Style.BOPOMOFO)
        bpmf_text = " ".join([p[0] for p in bpmf_list])
        
        if not bpmf_text.strip():
             await ctx.respond("轉換失敗，請確認輸入的是中文。")
             return

        font_size = 40
        padding = 20
        font = ImageFont.truetype(FONT_PATH, size=font_size)
        
        # 測量文字大小
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), bpmf_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width = text_width + (padding * 2)
        img_height = text_height + (padding * 2)

        # 建立圖片
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        
        # 繪製文字
        d.text(
            (padding, padding - bbox[1]),
            bpmf_text,
            font=font,
            fill="#FFFFFF"
        )

        # 儲存到記憶體並發送
        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            await ctx.respond(
                f"你說的「{text}」精靈語是：",
                file=discord.File(fp=image_binary, filename='elf.png')
            )

    except Exception as e:
        print(f"處理 /elf 指令時發生錯誤: {e}")
        await ctx.respond(f"糟糕，轉換時發生了錯誤！\n`{e}`")


# --- 2. Flask 網頁伺服器設定 (新增部分) ---
app = Flask(__name__)

# 建立一個簡單的首頁，讓 Render 知道程式正在運行
@app.route('/')
def home():
    # 這是 Render 的健康檢查 (Health Check) 會看到的
    return "Elf Discord Bot is active (Web Server Workaround)."

# 負責在背景啟動 Discord Bot 的函式
def run_bot():
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("!!! DISCORD_TOKEN 未設定。Bot 未啟動。")

# --- 3. 主執行區塊 ---
if __name__ == '__main__':
    # (A) 在背景執行緒啟動 Discord Bot
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # (B) 在主執行緒啟動 Flask 網頁伺服器 (Render 必需)
    # 獲取 Render 指定的通訊埠，否則使用 5000
    port = os.getenv("PORT", 5000) 
    
    print(f"Flask 網頁伺服器開始在通訊埠 {port} 監聽...")
    # 使用 gunicorn 來啟動 Flask，但由於我們在 if __name__ == '__main__': 區塊，
    # 為了簡化，我們將使用 Flask 內建的 run()，但設定時我們會使用 gunicorn。
    # app.run(host='0.0.0.0', port=port) # 實際 Render 上不使用此行

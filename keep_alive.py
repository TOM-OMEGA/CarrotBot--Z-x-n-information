from flask import Flask, request
from threading import Thread
import os
from collections import deque

# 狀態字典，main.py 會更新
bot_status = {
    "logged_in": False,
    "last_check": "尚未檢查",
    "last_post": "尚未發送"
}

# 最近紀錄（最多保存 10 筆）
log_history = deque(maxlen=10)

def add_log(message: str):
    print(message)  # 仍然會印到 Render Logs
    log_history.append(message)

app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Bot is alive!", 200

@app.route("/status", methods=["GET"])
def status():
    return {
        "bot_logged_in": bot_status["logged_in"],
        "last_check": bot_status["last_check"],
        "last_post": bot_status["last_post"]
    }, 200

@app.route("/logs", methods=["GET"])
def logs():
    return {
        "recent_logs": list(log_history)
    }, 200

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

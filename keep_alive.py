from flask import Flask
from threading import Thread
import os
from collections import deque
from facebook_scraper import get_posts

bot_status = {
    "logged_in": False,
    "last_check": "Not checked yet",
    "last_post": "No post sent yet"
}

log_history = deque(maxlen=10)

def add_log(message: str):
    print(message)
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

# 🔥 cookies 檢查路由
@app.route("/checkcookies", methods=["GET"])
def check_cookies():
    try:
        posts = list(get_posts("appledaily.tw", pages=1, cookies="cookies.json"))
        if not posts:
            add_log("⚠️ Cookies check failed: No posts fetched. Cookies may be expired.")
            return {"status": "fail", "reason": "No posts fetched. Cookies may be expired."}, 200
        else:
            post = posts[0]
            add_log(f"✅ Cookies check success: Got post_id={post.get('post_id')}")
            return {"status": "ok", "post_id": post.get("post_id")}, 200
    except Exception as e:
        add_log(f"❌ Cookies check error: {e}")
        return {"status": "error", "reason": str(e)}, 500

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

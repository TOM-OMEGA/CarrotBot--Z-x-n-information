import os
import json
import requests
import threading
from flask import Flask, jsonify, request

app = Flask(__name__)

# 讀取環境變數
RAILWAY_API_URL = os.getenv("RAILWAY_API_URL", "").strip()

# 記錄狀態
last_posts = []
cookie_exists = False


# -------------------------------
# ✅ 上傳 cookie 至 Railway
# -------------------------------
@app.route("/upload", methods=["POST"])
def upload_cookie():
    global cookie_exists
    try:
        if not RAILWAY_API_URL:
            return jsonify({"error": "缺少 RAILWAY_API_URL 環境變數"}), 500

        data = request.get_json(force=True)
        res = requests.post(f"{RAILWAY_API_URL}/upload", json=data, timeout=20)
        if res.status_code == 200:
            cookie_exists = True
            return jsonify({"message": "✅ Cookie 已更新"}), 200
        else:
            return jsonify({"error": f"Railway 回應錯誤：{res.text}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# ✅ 啟動爬蟲（轉發給 Railway）
# -------------------------------
@app.route("/run", methods=["GET"])
def run_scraper_api():
    if not RAILWAY_API_URL:
        return jsonify({"error": "缺少 RAILWAY_API_URL 環境變數"}), 500

    def run_remote_scraper():
        try:
            res = requests.get(f"{RAILWAY_API_URL}/run", timeout=10)
            print(f"🚀 Railway 爬蟲回應：{res.text}")
        except Exception as e:
            print(f"❌ 無法連線 Railway：{e}")

    threading.Thread(target=run_remote_scraper, daemon=True).start()
    return jsonify({"status": "ok", "message": "🚀 已啟動背景爬蟲，請稍候幾秒再查看 !fbstatus"}), 200


# -------------------------------
# ✅ 查詢爬蟲狀態（從 Railway 取得）
# -------------------------------
@app.route("/status", methods=["GET"])
def get_status():
    global last_posts
    if not RAILWAY_API_URL:
        return jsonify({"error": "缺少 RAILWAY_API_URL 環境變數"}), 500

    try:
        res = requests.get(f"{RAILWAY_API_URL}/status", timeout=15)
        if res.status_code == 200:
            posts = res.json()
            last_posts = posts
            return jsonify({
                "fb_state.json": cookie_exists,
                "posts_count": len(posts),
                "recent_posts": posts
            }), 200
        else:
            return jsonify({"error": f"Railway 回應錯誤：{res.text}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# ✅ Render 健康檢查首頁
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Render + Railway FB Scraper Controller",
        "status": "online",
        "railway_connected": bool(RAILWAY_API_URL)
    }), 200


# -------------------------------
# ✅ 主程式
# -------------------------------
def run_flask():
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Flask 已啟動於 port {port}")
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_flask()

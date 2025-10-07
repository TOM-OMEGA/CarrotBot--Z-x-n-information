# fb_scraper.py  (Render controller)
import os
import json
import threading
import logging
from time import sleep
from flask import Flask, request, jsonify
import requests

# -------------------------
# Config
# -------------------------
CRAWLER_URL = os.getenv("CRAWLER_URL", "").rstrip("/")  # e.g. https://your-repl-or-railway-url
API_KEY = os.getenv("API_KEY", None)  # optional simple auth for /upload from bot
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))  # seconds for HTTP calls
RETRY = int(os.getenv("REQUEST_RETRY", "1"))  # retry attempts for requests
RETRY_DELAY = float(os.getenv("REQUEST_RETRY_DELAY", "0.5"))  # seconds between retries

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)


# -------------------------
# Helpers
# -------------------------
def remote_post(path: str, json_body: dict, timeout: int = REQUEST_TIMEOUT):
    if not CRAWLER_URL:
        raise RuntimeError("CRAWLER_URL not configured")
    url = f"{CRAWLER_URL}{path}"
    last_exc = None
    for attempt in range(RETRY + 1):
        try:
            logging.info(f"POST -> {url} (attempt {attempt+1})")
            r = requests.post(url, json=json_body, timeout=timeout)
            return r
        except Exception as e:
            last_exc = e
            logging.warning(f"POST {url} failed (attempt {attempt+1}): {e}")
            sleep(RETRY_DELAY)
    raise last_exc


def remote_get(path: str, timeout: int = REQUEST_TIMEOUT):
    if not CRAWLER_URL:
        raise RuntimeError("CRAWLER_URL not configured")
    url = f"{CRAWLER_URL}{path}"
    last_exc = None
    for attempt in range(RETRY + 1):
        try:
            logging.info(f"GET -> {url} (attempt {attempt+1})")
            r = requests.get(url, timeout=timeout)
            return r
        except Exception as e:
            last_exc = e
            logging.warning(f"GET {url} failed (attempt {attempt+1}): {e}")
            sleep(RETRY_DELAY)
    raise last_exc


# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Render FB Scraper Controller",
        "status": "online",
        "crawler_configured": bool(CRAWLER_URL)
    })


@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts JSON body (cookie storage_state) from Discord bot and forwards to crawler /upload.
    Optional simple auth: include header X-API-KEY equal to API_KEY if configured.
    """
    # Basic auth (optional)
    if API_KEY:
        header_key = request.headers.get("X-API-KEY")
        if header_key != API_KEY:
            logging.warning("Unauthorized /upload attempt (bad API key)")
            return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.exception("Invalid JSON in /upload")
        return jsonify({"error": "invalid json", "detail": str(e)}), 400

    if not data:
        return jsonify({"error": "empty body"}), 400

    if not CRAWLER_URL:
        return jsonify({"error": "CRAWLER_URL not configured"}), 500

    try:
        resp = remote_post("/upload", data)
        return (resp.text, resp.status_code, {"Content-Type": "application/json"})
    except Exception as e:
        logging.exception("Forward /upload failed")
        return jsonify({"error": "forward failed", "detail": str(e)}), 502


@app.route("/run", methods=["GET"])
def run():
    """
    Trigger crawler to run. We call crawler /run asynchronously in background
    to avoid blocking Render/Discord on long operations.
    """
    if not CRAWLER_URL:
        return jsonify({"error": "CRAWLER_URL not configured"}), 500

    def fire_and_forget():
        try:
            logging.info("Triggering remote crawler /run")
            r = remote_get("/run", timeout=REQUEST_TIMEOUT)
            logging.info(f"Remote /run returned {r.status_code}: {r.text[:200]}")
        except Exception as e:
            logging.exception("Remote /run failed")

    threading.Thread(target=fire_and_forget, daemon=True).start()
    return jsonify({"message": "🚀 爬蟲已在背景啟動（轉發至爬蟲服務）"}), 200


@app.route("/status", methods=["GET"])
def status():
    """
    Query crawler service /status and return as-is (with small wrapper).
    """
    if not CRAWLER_URL:
        return jsonify({"error": "CRAWLER_URL not configured"}), 500

    try:
        resp = remote_get("/status", timeout=REQUEST_TIMEOUT)
        try:
            js = resp.json()
        except Exception:
            js = {"raw_text": resp.text}
        return jsonify({"ok": True, "crawler_url": CRAWLER_URL, "crawler_response": js}), 200
    except Exception as e:
        logging.exception("Status check failed")
        return jsonify({"ok": False, "error": str(e)}), 502


# -------------------------
# Simple endpoint to let Render or health-checkers wake us
# -------------------------
@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200


# -------------------------
# Start
# -------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logging.info(f"Starting fb_scraper controller on 0.0.0.0:{port}, forwarding to: {CRAWLER_URL}")
    app.run(host="0.0.0.0", port=port)

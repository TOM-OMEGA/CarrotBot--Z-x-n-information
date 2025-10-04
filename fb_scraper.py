from playwright.sync_api import sync_playwright
import os, requests
from flask import Flask, Response

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
app = Flask(__name__)

def send_to_discord(content):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": content})

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="fb_state.json")
        page = context.new_page()

        page.goto("https://www.facebook.com/appledaily.tw/posts")
        page.wait_for_selector('div[role="article"]', timeout=10000)
        articles = page.query_selector_all('div[role="article"]')
        for a in articles[:3]:
            text = a.inner_text()
            send_to_discord(f"📢 新貼文：\n{text[:200]}...")

@app.route("/run", methods=["GET"])
def run():
    run_scraper()
    return Response("✅ 執行完成", status=200)

@app.route("/health", methods=["GET"])
def health():
    return Response("OK", status=200)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

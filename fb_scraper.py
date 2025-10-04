from playwright.sync_api import sync_playwright
import os, requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_to_discord(content):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": content})

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

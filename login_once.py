# login_once.py
from playwright.sync_api import sync_playwright
import json, os

def login_once():
    print("🌍 啟動瀏覽器，登入 Facebook")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 手動登入要可視化
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.facebook.com/login")
        input("🧭 請手動登入 Facebook，登入後按下 Enter 以繼續...")
        storage = context.storage_state()
        with open("fb_state.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(storage))
        print("✅ Cookie 已儲存為 fb_state.json")
        browser.close()

if __name__ == "__main__":
    login_once()

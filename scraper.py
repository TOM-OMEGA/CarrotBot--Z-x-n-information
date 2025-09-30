import requests
from bs4 import BeautifulSoup
import json
import os

# 目標粉專網址（公開頁面）
PAGE_URL = "https://www.facebook.com/appledaily.tw/posts"

# 從環境變數讀取 Discord Webhook URL
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# 已推送紀錄檔
HISTORY_FILE = "posted.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False, indent=2)

def fetch_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(PAGE_URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.find_all("div", {"role": "article"})

def send_to_discord(content):
    if not WEBHOOK_URL:
        print("❌ 沒有設定 DISCORD_WEBHOOK_URL")
        return
    payload = {"content": content}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    history = load_history()
    posts = fetch_posts()
    new_ids = []

    for post in posts[:5]:  # 只抓前 5 篇
        post_id = post.get("data-ft")
        if not post_id:
            continue

        if post_id not in history:
            text = post.get_text(separator="\n", strip=True)
            preview = text[:200] + "..." if len(text) > 200 else text
            send_to_discord(f"📢 新貼文：\n{preview}")
            new_ids.append(post_id)

    if new_ids:
        history.update(new_ids)
        save_history(history)
        print(f"✅ 推送 {len(new_ids)} 篇新貼文到 Discord")
    else:
        print("ℹ️ 沒有新貼文")

if __name__ == "__main__":
    main()

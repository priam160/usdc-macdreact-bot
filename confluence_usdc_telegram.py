import os
import requests

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT  = os.environ.get("TG_CHAT")

def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        print("Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT, "text": msg})

if __name__ == "__main__":
    send_telegram("✅ TEST OK — GitHub Actions + Telegram fonctionnent")
    print("Message Telegram envoyé")

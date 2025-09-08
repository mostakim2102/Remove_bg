from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
REMOVE_BG_API_KEY = os.environ.get("REMOVE_BG_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" not in data:
        return "ok"

    message = data["message"]
    chat_id = message["chat"]["id"]

    # যদি ছবি পাঠানো হয়
    if "photo" in message:
        file_id = message["photo"][-1]["file_id"]
        file_info = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}").json()

        if "result" not in file_info:
            send_message(chat_id, "❌ ছবি আনতে সমস্যা হয়েছে।")
            return "ok"

        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

        # remove.bg এ পাঠানো
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            data={"image_url": file_url, "size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
        )

        if response.status_code == 200:
            files = {"photo": ("no-bg.png", response.content)}
            requests.post(f"{TELEGRAM_API}/sendPhoto", data={"chat_id": chat_id}, files=files)
        else:
            send_message(chat_id, "❌ ব্যাকগ্রাউন্ড রিমুভ করতে সমস্যা হয়েছে।")

    # যদি টেক্সট মেসেজ পাঠানো হয়
    elif "text" in message:
        text = message["text"].lower()

        if text == "/start":
            send_message(chat_id, "👋 হাই! আমাকে ছবি পাঠান, আমি ব্যাকগ্রাউন্ড মুছে দিব।")

        elif text == "/share":
            bot_username = os.environ.get("bgremovvbot")  # vercel env এ সেট করবেন
            if not bot_username:
                send_message(chat_id, "⚠️ BOT_USERNAME সেট করা হয়নি।")
                return "ok"

            share_link = f"https://t.me/{bot_username}"
            button = {
                "inline_keyboard": [
                    [
                        {
                            "text": "Share ♻️",
                            "switch_inline_query": f"Check out this bot 👉 {share_link}",
                        }
                    ]
                ]
            }
            url = f"{TELEGRAM_API}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": "📢 আপনার বন্ধুদের বটটি শেয়ার করুন 🎉",
                "reply_markup": button,
            }
            requests.post(url, json=payload)

        else:
            send_message(chat_id, "📸 শুধু একটি ছবি পাঠান।")

    return "ok"

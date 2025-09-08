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
    else:
        if "text" in message and message["text"].lower() == "/start":
            send_message(chat_id, "👋 হাই! আমাকে ছবি পাঠান, আমি ব্যাকগ্রাউন্ড মুছে দিব।")
        else:
            send_message(chat_id, "📸 শুধু একটি ছবি পাঠান।")

    return "ok"

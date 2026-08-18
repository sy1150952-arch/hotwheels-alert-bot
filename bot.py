import os
import time
import urllib.parse
import urllib.request
import json

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

PRODUCT_ID = "787950"
PRODUCT_URL = f"https://blinkit.com/prn/x/prid/{PRODUCT_ID}"

LUCKNOW_PIN = "226004"


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        encoded = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, data=encoded, method="POST")
    else:
        request = urllib.request.Request(url)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def send_message(chat_id, text):
    telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        },
    )


def main():
    offset = None

    print("Telegram bot started.")

    while True:
        try:
            params = {"timeout": 20}

            if offset is not None:
                params["offset"] = offset

            result = telegram("getUpdates", params)

            if not result.get("ok"):
                time.sleep(5)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                text = message.get("text", "").strip()

                if not chat_id:
                    continue

                if text == "/start":
                    send_message(
                        chat_id,
                        "🔥 Hot Wheels Alert Bot\n\n"
                        "Commands:\n"
                        "/check - Hot Wheels product check\n"
                        "/link - Blinkit product link\n"
                        "/help - Help",
                    )

                elif text == "/help":
                    send_message(
                        chat_id,
                        "📌 Hot Wheels Bot\n\n"
                        "/check → Product information\n"
                        "/link → Blinkit product link\n\n"
                        f"📍 PIN: {LUCKNOW_PIN}"
                    )

                elif text == "/link":
                    send_message(
                        chat_id,
                        "🔥 Hot Wheels product\n\n"
                        f"Product ID: {PRODUCT_ID}\n"
                        f"📍 PIN: {LUCKNOW_PIN}\n\n"
                        f"Open Blinkit:\n{PRODUCT_URL}"
                    )

                elif text == "/check":
                    send_message(
                        chat_id,
                        "🔎 Hot Wheels check\n\n"
                        f"Product ID: {PRODUCT_ID}\n"
                        f"📍 Lucknow - {LUCKNOW_PIN}\n\n"
                        "Blinkit stock is location/session dependent, "
                        "so this bot will not guess stock status.\n\n"
                        "👉 Open the product and check whether "
                        "ADD / Buy is available:\n"
                        f"{PRODUCT_URL}"
                    )

                else:
                    send_message(
                        chat_id,
                        "Unknown command.\n\n"
                        "Use /check or /link"
                    )

        except Exception as e:
            print("Bot error:", repr(e))
            time.sleep(5)


if __name__ == "__main__":
    main()

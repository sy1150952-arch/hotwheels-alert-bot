
import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

message = """🚗🔥 HOT WHEELS ALERT BOT

✅ Telegram connection successful!

📍 Location: Lucknow
📮 PIN: 226004

Bot is ready for stock checking.
"""

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=20
)

print(response.text)

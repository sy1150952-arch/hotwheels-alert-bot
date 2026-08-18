import os
import time
import json
import urllib.parse
import urllib.request

# =========================
# SETTINGS
# =========================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BLINKIT_API_KEY = os.environ.get("BLINKIT_API_KEY")

PRODUCT_ID = "787950"
PRODUCT_URL = "https://blinkit.com/prn/x/prid/787950"
PINCODE = "226004"
CITY = "Lucknow"

# Search text used by Blinkit Search API
SEARCH_QUERY = "Hot Wheels Subaru Impreza WRX"

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
MINDCASE_API = "https://api.mindcase.co/v1/data/blinkit/search/run"

# Check every 5 minutes
CHECK_INTERVAL = 300


# =========================
# TELEGRAM
# =========================

def telegram(method, data=None):
    url = f"{TELEGRAM_API}/{method}"

    if data:
        encoded = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(
            url,
            data=encoded,
            method="POST"
        )
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
            "disable_web_page_preview": False
        }
    )


# =========================
# BLINKIT CHECK
# =========================

def check_blinkit():
    headers = {
        "Authorization": f"Bearer {BLINKIT_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "params": {
            "query": SEARCH_QUERY,
            "city": CITY,
            "pincode": PINCODE
        }
    }

    data = json.dumps(payload).encode()

    request = urllib.request.Request(
        MINDCASE_API,
        data=data,
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode())


# =========================
# FIND PRODUCT
# =========================

def find_product(data):
    """
    Mindcase response structure can change.
    This function searches recursively for a product
    whose Product ID / Variant ID matches 787950.
    """

    if isinstance(data, list):
        for item in data:
            result = find_product(item)
            if result:
                return result

    elif isinstance(data, dict):

        product_id = str(
            data.get("Product ID", "")
        )

        variant_id = str(
            data.get("Variant ID", "")
        )

        if product_id == PRODUCT_ID or variant_id == PRODUCT_ID:
            return data

        for value in data.values():
            result = find_product(value)
            if result:
                return result

    return None


# =========================
# STOCK STATUS
# =========================

def get_stock_status():

    data = check_blinkit()

    product = find_product(data)

    if not product:
        return {
            "found": False,
            "in_stock": False,
            "stock_count": 0,
            "product": None
        }

    in_stock = product.get("In Stock", False)

    stock_count = product.get(
        "Stock Count",
        0
    )

    try:
        stock_count = int(stock_count)
    except:
        stock_count = 0

    return {
        "found": True,
        "in_stock": bool(in_stock),
        "stock_count": stock_count,
        "product": product
    }


# =========================
# MAIN BOT
# =========================

def main():

    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN secret missing")
        return

    if not BLINKIT_API_KEY:
        print("ERROR: BLINKIT_API_KEY secret missing")
        return

    print("Hot Wheels Telegram Bot started.")

    offset = None
    last_chat_id = None

    # Prevent repeated alerts while stock remains available
    already_alerted = False

    last_check = 0

    while True:

        try:

            # -------------------------
            # TELEGRAM MESSAGES
            # -------------------------

            params = {
                "timeout": 20
            }

            if offset is not None:
                params["offset"] = offset

            result = telegram(
                "getUpdates",
                params
            )

            if result.get("ok"):

                for update in result.get("result", []):

                    offset = update["update_id"] + 1

                    message = update.get(
                        "message",
                        {}
                    )

                    chat = message.get(
                        "chat",
                        {}
                    )

                    chat_id = chat.get("id")

                    text = message.get(
                        "text",
                        ""
                    ).strip()

                    if not chat_id:
                        continue

                    last_chat_id = chat_id

                    # -------------------------
                    # /START
                    # -------------------------

                    if text == "/start":

                        send_message(
                            chat_id,
                            "🚗 Hot Wheels Stock Alert Bot\n\n"
                            "Commands:\n"
                            "/check - Check Hot Wheels stock\n"
                            "/link - Blinkit product link\n"
                            "/help - Help\n\n"
                            f"📍 {CITY} - {PINCODE}"
                        )

                    # -------------------------
                    # /HELP
                    # -------------------------

                    elif text == "/help":

                        send_message(
                            chat_id,
                            "📌 Hot Wheels Bot\n\n"
                            "/check → Live stock check\n"
                            "/link → Blinkit product\n"
                            "/help → Help\n\n"
                            f"📍 Location: {CITY}\n"
                            f"PIN: {PINCODE}"
                        )

                    # -------------------------
                    # /LINK
                    # -------------------------

                    elif text == "/link":

                        send_message(
                            chat_id,
                            "🚗 Hot Wheels Product\n\n"
                            f"Product ID: {PRODUCT_ID}\n"
                            f"📍 {CITY} - {PINCODE}\n\n"
                            f"{PRODUCT_URL}"
                        )

                    # -------------------------
                    # /CHECK
                    # -------------------------

                    elif text == "/check":

                        send_message(
                            chat_id,
                            "🔎 Checking Blinkit stock..."
                        )

                        try:

                            status = get_stock_status()

                            if not status["found"]:

                                send_message(
                                    chat_id,
                                    "⚠️ Product ID "
                                    f"{PRODUCT_ID} "
                                    "was not found in the "
                                    "Blinkit search results.\n\n"
                                    "This does NOT necessarily mean "
                                    "the product is out of stock.\n\n"
                                    f"👉 {PRODUCT_URL}"
                                )

                            elif status["in_stock"]:

                                send_message(
                                    chat_id,
                                    "🚨 HOT WHEELS IN STOCK! 🚨\n\n"
                                    "🚗 Hot Wheels Subaru-Impreza WRX\n\n"
                                    f"Product ID: {PRODUCT_ID}\n"
                                    f"📦 Stock: {status['stock_count']}\n"
                                    f"📍 {CITY} - {PINCODE}\n\n"
                                    "👉 BUY NOW:\n"
                                    f"{PRODUCT_URL}"
                                )

                            else:

                                send_message(
                                    chat_id,
                                    "❌ Currently OUT OF STOCK\n\n"
                                    f"Product ID: {PRODUCT_ID}\n"
                                    f"📍 {CITY} - {PINCODE}\n\n"
                                    "I'll keep checking automatically.\n\n"
                                    f"{PRODUCT_URL}"
                                )

                        except Exception as e:

                            print(
                                "Manual check error:",
                                repr(e)
                            )

                            send_message(
                                chat_id,
                                "⚠️ Stock check failed.\n"
                                "Please try again in a moment."
                            )

                    else:

                        send_message(
                            chat_id,
                            "Unknown command.\n\n"
                            "Use /check or /help"
                        )

            # -------------------------
            # AUTOMATIC CHECK
            # -------------------------

            current_time = time.time()

            if (
                last_chat_id
                and current_time - last_check >= CHECK_INTERVAL
            ):

                last_check = current_time

                try:

                    print(
                        "Automatic Blinkit stock check..."
                    )

                    status = get_stock_status()

                    print(
                        "Product found:",
                        status["found"]
                    )

                    print(
                        "In stock:",
                        status["in_stock"]
                    )

                    print(
                        "Stock count:",
                        status["stock_count"]
                    )

                    # Alert only when stock becomes available
                    if (
                        status["found"]
                        and status["in_stock"]
                        and not already_alerted
                    ):

                        send_message(
                            last_chat_id,
                            "🚨🚨 HOT WHEELS STOCK ALERT 🚨🚨\n\n"
                            "🚗 Hot Wheels Subaru-Impreza WRX "
                            "Die Cast Car\n\n"
                            f"📦 Stock: {status['stock_count']}\n"
                            f"📍 {CITY} - {PINCODE}\n\n"
                            "🔥 PRODUCT IS AVAILABLE!\n\n"
                            "👉 BUY NOW:\n"
                            f"{PRODUCT_URL}"
                        )

                        already_alerted = True

                    # Reset after it goes out of stock
                    elif (
                        status["found"]
                        and not status["in_stock"]
                    ):

                        already_alerted = False

                except Exception as e:

                    print(
                        "Automatic check error:",
                        repr(e)
                    )

            time.sleep(1)

        except Exception as e:

            print(
                "Bot error:",
                repr(e)
            )

            time.sleep(10)


if __name__ == "__main__":
    main()

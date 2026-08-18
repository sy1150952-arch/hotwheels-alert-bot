import os
import re
import requests
from playwright.sync_api import sync_playwright

PRODUCT_ID = "787950"
PRODUCT_URL = f"https://blinkit.com/prn/x/prid/{PRODUCT_ID}"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=30,
    )

    response.raise_for_status()


def check_stock():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = browser.new_page(
            viewport={
                "width": 1280,
                "height": 900,
            },
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        try:
            print("Opening Blinkit product page...")

            page.goto(
                PRODUCT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(8000)

            text = page.locator("body").inner_text().lower()

            print("Page loaded.")
            print("URL:", page.url)

            # Save page text for debugging
            with open("blinkit_page.txt", "w", encoding="utf-8") as f:
                f.write(text)

            # Stock indicators
            add_available = bool(
                re.search(r"\badd\b", text)
                or re.search(r"\bbuy now\b", text)
                or re.search(r"\bbuy\b", text)
            )

            out_of_stock = (
                "out of stock" in text
                or "currently unavailable" in text
                or "not available" in text
            )

            if add_available and not out_of_stock:
                print("STOCK MAY BE AVAILABLE!")

                message = (
                    "🚨 HOT WHEELS STOCK ALERT 🚨\n\n"
                    "🔥 Stock may be AVAILABLE!\n\n"
                    f"Product ID: {PRODUCT_ID}\n"
                    "📍 Lucknow - PIN 226004\n\n"
                    f"👉 Open Blinkit:\n{PRODUCT_URL}\n\n"
                    "⚡ Check and order quickly!"
                )

                send_telegram(message)
                print("Telegram alert sent.")

            else:
                print("No stock detected.")

        except Exception as e:
            print("Checker error:", repr(e))
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    check_stock()

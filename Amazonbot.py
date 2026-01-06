import os
import time
import logging
import requests
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime

# =====================
# CONFIG (Secrets)
# =====================
TELEGRAM_TOKEN = os.getenv("8554166435:AAHnRljnZlYMo-K2evqFQQOZPQ3xZeawtGw")
TELEGRAM_CHAT_ID = os.getenv("-5011942387")

CHECK_INTERVAL = 180  # saniye (3 dk)

URLS = [
    "https://www.amazon.com.tr/gp/goldbox",              # Deals
    "https://www.amazon.com.tr/gp/bestsellers"           # Bestsellers
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# =====================
# LOGGING
# =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# =====================
# HELPERS
# =====================
def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ Telegram secrets eksik")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logging.error(f"Telegram hata: {e}")


def check_stock(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")

    texts = soup.get_text(" ").lower()

    out_phrases = [
        "stokta yok",
        "tükendi",
        "geçici olarak temin edilemiyor"
    ]

    for phrase in out_phrases:
        if phrase in texts:
            return False

    return True


# =====================
# MAIN LOOP
# =====================
def run():
    scraper = cloudscraper.create_scraper()

    logging.info("🚀 Amazon Avcı V3.1 başlatıldı")

    while True:
        for url in URLS:
            try:
                label = "Deals" if "goldbox" in url else "Bestsellers"
                logging.info(f"🔍 Keşif: {label}")

                r = scraper.get(url, headers=HEADERS, timeout=20)
                stock_ok = check_stock(r.text)

                logging.info(
                    f"Ürün | STOCK_RAW='{''}' | BOOL={stock_ok}"
                )

                if stock_ok:
                    msg = (
                        "🔥 <b>STOK YAKALANDI!</b>\n\n"
                        f"📍 {label}\n"
                        f"🔗 {url}\n"
                        f"🕒 {datetime.now().strftime('%H:%M:%S')}"
                    )
                    send_telegram(msg)

                time.sleep(5)

            except Exception as e:
                logging.error(f"Hata ({url}): {e}")

        logging.info("✅ Tur tamamlandı")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()

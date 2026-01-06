import requests
import time
import logging
import signal
import sys
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ================== AYARLAR ==================

CHECK_INTERVAL = 180  # saniye (3 dk)
COOLDOWN_MINUTES = 180  # aynı ürün için tekrar bildirim süresi
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

AMAZON_URLS = {
    "Deals": "https://www.amazon.com.tr/gp/goldbox",
    "Bestsellers": "https://www.amazon.com.tr/gp/bestsellers",
}

TELEGRAM_BOT_TOKEN = "8554166435:AAH_tfMqzU_hxkko2JLjBNOL4a9f2WHcBlI"
TELEGRAM_CHAT_ID = "-5011942387"

# ================== LOG ==================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logger = logging.getLogger()

# ================== GLOBAL STATE ==================

last_stock_state = {}
last_notify_time = {}
running = True

# ================== SIGNAL ==================

def shutdown_handler(sig, frame):
    global running
    logger.info("⚠️ Signal alındı, bot kapatılıyor...")
    running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ================== TELEGRAM ==================

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        logger.info(f"Telegram gönderilemedi: {e}")

# ================== STOCK PARSE ==================

def is_in_stock(text: str) -> bool:
    if not text:
        return False

    t = text.lower()
    return any(x in t for x in [
        "stokta",
        "in stock",
        "order soon",
        "sadece",
        "only"
    ])

# ================== COOLDOWN ==================

def can_notify(key):
    now = datetime.now()
    last = last_notify_time.get(key)
    if not last:
        return True
    return now - last > timedelta(minutes=COOLDOWN_MINUTES)

# ================== AMAZON SCRAPER ==================

def scan_page(name, url):
    logger.info(f"🔍 Keşif: {name}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        products = soup.select("div[data-asin]")
        for p in products:
            asin = p.get("data-asin")
            if not asin:
                continue

            title_tag = p.select_one("h2 span")
            title = title_tag.text.strip() if title_tag else "Ürün"

            stock_tag = p.select_one("span.a-color-success, span.a-color-state")
            stock_text = stock_tag.text.strip() if stock_tag else ""

            in_stock = is_in_stock(stock_text)

            prev = last_stock_state.get(asin, False)
            last_stock_state[asin] = in_stock

            logger.info(f"{title[:50]} | STOCK_RAW='{stock_text}' | BOOL={in_stock}")

            if in_stock and not prev and can_notify(asin):
                send_telegram(
                    f"🔥 <b>ÜRÜN STOĞA GİRDİ</b>\n\n"
                    f"{title}\n\n"
                    f"{url}"
                )
                last_notify_time[asin] = datetime.now()

    except Exception as e:
        logger.info(f"Sayfa hatası ({name}): {e}")

# ================== MAIN LOOP ==================

def main():
    logger.info("🚀 Amazon Avcı Botu BAŞLADI")

    while running:
        for name, url in AMAZON_URLS.items():
            if not running:
                break
            scan_page(name, url)
            time.sleep(5)

        logger.info("✅ Tur tamamlandı")
        sleep_left = CHECK_INTERVAL
        while sleep_left > 0 and running:
            time.sleep(1)
            sleep_left -= 1

    logger.info("🛑 Bot tamamen durdu")

# ================== RUN ==================

if __name__ == "__main__":
    main()

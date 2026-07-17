import asyncio
import re
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# ============ CONFIG ============
URL = "https://trouverunlogement.lescrous.fr/tools/47/search?bounds=3.8070597_43.6533542_3.9413208_43.5667088&locationName=Montpellier"

# Les valeurs viennent des "secrets" GitHub (voir instructions), pas écrites en dur ici
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
# ==================================


async def get_page_text():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        text = await page.inner_text("body")
        await browser.close()
        return text


def extract_count(text):
    if "Aucun logement trouvé" in text:
        return 0
    match = re.search(r"(\d+)\s+logements?\s+trouvés?", text)
    if match:
        return int(match.group(1))
    return None


def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(telegram_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    resp.raise_for_status()
    print(f"[{datetime.now()}] Notification Telegram envoyée.")


async def check_once():
    text = await get_page_text()
    count = extract_count(text)

    if count is None:
        print(f"[{datetime.now()}] ATTENTION : format de page non reconnu.")
    elif count > 0:
        print(f"[{datetime.now()}] >>> {count} logement(s) trouvé(s) à Montpellier !")
        send_telegram_message(
            f"🏠 {count} logement(s) CROUS disponible(s) à Montpellier !\n\n"
            f"Vérifie ici : {URL}\n\n"
            f"Détecté le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        )
    else:
        print(f"[{datetime.now()}] Rien de nouveau (0 logement trouvé).")


if __name__ == "__main__":
    asyncio.run(check_once())

import os
import io
import asyncio
import random
import requests
from telegram import Bot
from dotenv import load_dotenv
from urllib.parse import quote as safely_quote
from PIL import Image
from datetime import datetime, timedelta

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
JUPITER_REFERRAL_KEY = os.getenv('JUPITER_REFERRAL_KEY')
IMAGE_DIRECTORY = os.path.abspath('/root/advisoorbot/Memes')
excluded_symbols = ["ETH", "SOL", "WAVAX", "WSOL", "BTC", "WBTC","BONK"]

def get_random_image_path(image_directory):
    if not os.path.exists(image_directory):
        os.makedirs(image_directory, exist_ok=True)
        return None
    
    images = [os.path.join(image_directory, file) for file in os.listdir(image_directory) if file.endswith(('.png', '.jpg', '.jpeg'))]
    if images:
        return random.choice(images)
    else:
        return None

async def send_telegram_message(bot, chat_id, text, image_path=None):
    if image_path:
        try:
            with Image.open(image_path) as img:
                img = img.resize((200, 200), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img_format = 'JPEG' if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg') else 'PNG'
                img.save(buf, format=img_format)
                buf.seek(0)
                await bot.send_photo(chat_id=chat_id, photo=buf, caption=text, parse_mode='HTML')
        except Exception as e:
            print(f"Error resizing or sending image: {e}")
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_check_times = {address: datetime.now() - timedelta(minutes=1) for address in TARGET_ADDRESSES}
    last_checked_ids = {address: None for address in TARGET_ADDRESSES}
    
    # Fetch initial last transactions for each address
    initial_transactions = []
    for address in TARGET_ADDRESSES:
        transactions = await fetch_new_transactions(address, None)
        if transactions:
            initial_transactions.extend(transactions)
            last_checked_ids[address] = transactions[0].get('id')
    if initial_transactions:
        message = await create_message(initial_transactions)
        image_path = get_random_image_path(IMAGE_DIRECTORY)
        await send_telegram_message(bot, CHAT_ID, message, image_path)

    # Main loop to monitor for future transactions
    while True:
        current_time = datetime.now()
        for address in TARGET_ADDRESSES:
            if current_time - last_check_times[address] >= timedelta(minutes=1):
                new_transactions = await fetch_new_transactions(address, last_checked_ids[address])
                if new_transactions:
                    message = await create_message(new_transactions)
                    image_path = get_random_image_path(IMAGE_DIRECTORY)
                    await send_telegram_message(bot, CHAT_ID, message, image_path)
                    last_checked_ids[address] = new_transactions[0].get('id')
                last_check_times[address] = current_time
        await asyncio.sleep(60)  # Wait for a minute before the next check

asyncio.run(main())

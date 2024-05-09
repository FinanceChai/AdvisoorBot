import os
import io
import asyncio
import random
import aiohttp
from dotenv import load_dotenv
from telegram import Bot
from PIL import Image
from urllib.parse import quote as safely_quote

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
IMAGE_DIRECTORY = os.path.abspath('/root/advisoorbot/Memes')
EXCLUDED_SYMBOLS = {"ETH", "SOL", "BTC", "BONK"}  # Add or modify as necessary

def get_random_image_path(image_directory):
    if not os.path.exists(image_directory):
        os.makedirs(image_directory, exist_ok=True)
        return None
    images = [os.path.join(image_directory, file) for file in os.listdir(image_directory) if file.endswith(('.png', '.jpg', '.jpeg'))]
    return random.choice(images) if images else None

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/meta?tokenAddress={safely_quote(token_address)}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
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
                await bot.send_photo(chat_id, photo=buf, caption=text, parse_mode='HTML')
        except Exception as e:
            print(f"Error resizing or sending image: {e}")
            await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await bot.send_message(chat_id, text=text, parse_mode='HTML')

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    async with aiohttp.ClientSession() as session:
        last_signature = {address: None for address in TARGET_ADDRESSES}
        for address in TARGET_ADDRESSES:
            transaction_details = await fetch_last_spl_transactions(session, address, None)
            if transaction_details:
                last_signature[address] = transaction_details['signature']

        while True:
            await asyncio.sleep(60)
            for address in TARGET_ADDRESSES:
                transaction_details = await fetch_last_spl_transactions(session, address, last_signature[address])
                if transaction_details:
                    new_signature = transaction_details['signature']
                    transactions = [transaction_details]  # List expected by create_message
                    message = await create_message(session, transactions)
                    if message:
                        image_path = get_random_image_path(IMAGE_DIRECTORY)
                        await send_telegram_message(bot, CHAT_ID, message, image_path)
                    last_signature[address] = new_signature

if __name__ == "__main__":
    asyncio.run(main())

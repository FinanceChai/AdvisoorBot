import os
import io
import asyncio
import random
import aiohttp
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
excluded_symbols = ["ETH", "SOL", "WAVAX", "WSOL", "BTC", "WBTC", "BONK"]

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
                await bot.send_photo(chat_id, photo=buf, caption=text, parse_mode='HTML')
        except Exception as e:
            print(f"Error resizing or sending image: {e}")
            await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)

async def fetch_last_spl_transactions(session, address, last_signatures):
    params = {'account': address, 'limit': 5, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        new_transactions = []
        if response.status == 200:
            data = await response.json()
            for transaction in data.get('data', []):
                signature = transaction.get('signature', '')
                if isinstance(signature, list):
                    signature = signature[0] if signature else ''
                if signature and signature not in last_signatures:
                    new_transactions.append(transaction)
                    last_signatures.add(signature)
    return new_transactions

async def create_message(transactions):
    message_lines = ["🎱 8 Ball Shakes 🎱\n\n"]
    for transaction in transactions:
        token_symbol = transaction.get('tokenSymbol', 'Unknown')
        if token_symbol in excluded_symbols:
            continue
        token_name = transaction.get('tokenName', 'Unknown')
        token_address = transaction.get('tokenAddress', 'Unknown')
        owner_address = transaction.get('owner', 'Unknown')
        message_lines.append(
            f"Token Name: {token_name}\n"
            f"Token Symbol: {token_symbol}\n"
            f"<a href='https://solscan.io/token/{safely_quote(token_address)}'>Token Contract</a>\n"
            f"<a href='https://solscan.io/account/{safely_quote(owner_address)}'>Owner Wallet</a>\n\n"
        )
    return '\n'.join(message_lines)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signatures = {address: set() for address in TARGET_ADDRESSES}

    async with aiohttp.ClientSession() as session:
        # Initial fetch of transactions
        for address in TARGET_ADDRESSES:
            transactions = await fetch_last_spl_transactions(session, address, last_signatures[address])
            if transactions:
                message = await create_message(transactions)
                image_path = get_random_image_path(IMAGE_DIRECTORY)
                await send_telegram_message(bot, CHAT_ID, message, image_path)

        # Continuous monitoring of new transactions
        while True:
            await asyncio.sleep(60)  # Wait for a minute before the next cycle
            for address in TARGET_ADDRESSES:
                transactions = await fetch_last_spl_transactions(session, address, last_signatures[address])
                if transactions:
                    message = await create_message(transactions)
                    image_path = get_random_image_path(IMAGE_DIRECTORY)
                    await send_telegram_message(bot, CHAT_ID, message, image_path)

if __name__ == "__main__":
    asyncio.run(main())

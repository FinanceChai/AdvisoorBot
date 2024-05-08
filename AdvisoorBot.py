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

async def fetch_new_transactions(session, address, last_checked_id):
    transactions = []
    url = f"https://api.solanabeach.io/v1/accounts/{address}/transactions?before={last_checked_id}&limit=1"
    headers = {"Authorization": f"Bearer {SOLSCAN_API_KEY}"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            for result in data['transactions']:
                transaction = {
                    'id': result['txid'],
                    'symbol': result['operation']['symbol'],
                    'tokenName': result['operation']['tokenName'],
                    'tokenAddress': result['operation']['tokenAddress'],
                    'owner': result['operation']['owner']
                }
                transactions.append(transaction)
    return transactions

async def create_message(transactions):
    message_lines = ["🎱 8 Ball Shakes 🎱\n\n"]
    for transaction in transactions:
        if transaction['symbol'] in excluded_symbols:
            continue
        message_lines.append(
            f"Token Name: {transaction['tokenName']}\n"
            f"Token Symbol: {transaction['symbol']}\n"
            f"<a href='https://solscan.io/token/{safely_quote(transaction['tokenAddress'])}'>CA</a>\n"
            f"<a href='https://solscan.io/account/{safely_quote(transaction['owner'])}'>Buyer Wallet</a>\n\n"
            f"<a href='https://www.dextools.io/app/en/solana/pair-explorer/{safely_quote(transaction['tokenAddress'])}'>View Pair on DexScreener</a>\n"
            f"<a href='https://jup.ag/swap/SOL-{safely_quote(transaction['tokenAddress'])}'>Buy on Jupiter</a>\n\n"
        )
    return '\n'.join(message_lines)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_checked_ids = {address: None for address in TARGET_ADDRESSES}

    async with aiohttp.ClientSession() as session:
        # Initial fetch of transactions
        for address in TARGET_ADDRESSES:
            transactions = await fetch_new_transactions(session, address, None)
            if transactions:
                message = await create_message(transactions)
                image_path = get_random_image_path(IMAGE_DIRECTORY)
                await send_telegram_message(bot, CHAT_ID, message, image_path)
                last_checked_ids[address] = transactions[0]['id']

        # Continuous monitoring of new transactions
        while True:
            await asyncio.sleep(60)  # Wait for a minute before the next cycle
            for address in TARGET_ADDRESSES:
                transactions = await fetch_new_transactions(session, address, last_checked_ids[address])
                if transactions:
                    message = await create_message(transactions)
                    image_path = get_random_image_path(IMAGE_DIRECTORY)
                    await send_telegram_message(bot, CHAT_ID, message, image_path)
                    last_checked_ids[address] = transactions[0]['id']

if __name__ == "__main__":
    asyncio.run(main())

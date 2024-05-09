import os
import io
import asyncio
import random
import aiohttp
from telegram import Bot
from dotenv import load_dotenv
from urllib.parse import quote as safely_quote
from PIL import Image

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
IMAGE_DIRECTORY = os.path.abspath('/root/advisoorbot/Memes')
EXCLUDED_SYMBOLS = {"ETH", "SOL", "BTC", "BONK", "WAVAX", "WETH", "WBTC", "Bonk", "bonk"}

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
            with Image.open(image_path) as img:  # Ensure that image_path is the variable used
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

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/list?mintAddress={safely_quote(token_address)}&limit=1"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data['data']:
                token_info = data['data'][0]
                
                return {
                    'symbol': token_info.get('tokenSymbol', 'Unknown'),
                    'name': token_info.get('tokenName', 'Unknown'),
                    'market_cap': token_info.get('marketCapFD', 'Unknown')
                }
        return {'symbol': 'Unknown', 'name': 'Unknown', 'market_cap': 'Unknown'}

async def fetch_last_spl_transactions(session, address, last_signature):
    params = {'account': address, 'limit': 1, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('data') and data['data'][0]['signature'] != last_signature:
                return data['data'][0]
    return None

async def create_message(session, transactions):
    message_lines = ["🎱 New Transactions 🎱\n\n"]
    for transaction in transactions:
        token_metadata = await fetch_token_metadata(session, transaction['mintAddress'])
        token_symbol = token_metadata['tokenSymbol']
        token_name = token_metadata['tokenName']
        market_cap = token_metadata['marketCapFD']

        if token_symbol in EXCLUDED_SYMBOLS:
            continue
        
        token_address = transaction.get('mintAddress', 'Unknown')
        owner_address = transaction.get('owner', 'Unknown')
        message_lines.append(
            f"Token Name: {token_name}\n"
            f"Token Symbol: {token_symbol}\n"
            f"Fully Diluted Market Cap: ${market_cap:,.2f}\n"
            f"<a href='https://solscan.io/token/{safely_quote(token_address)}'>Token Contract</a>\n"
            f"<a href='https://solscan.io/account/{safely_quote(owner_address)}'>Owner Wallet</a>\n\n"
        )
    return '\n'.join(message_lines) if len(message_lines) > 1 else None

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signature = {address: None for address in TARGET_ADDRESSES}
    async with aiohttp.ClientSession() as session:
        # Initial fetch of transactions and update last known signatures
        for address in TARGET_ADDRESSES:
            transaction = await fetch_last_spl_transactions(session, address, last_signature[address])
            if transaction:
                last_signature[address] = transaction['signature']

        # Continuous monitoring of new transactions every minute
        while True:
            await asyncio.sleep(60)  # Wait for a minute before checking new transactions
            new_transactions = []
            for address in TARGET_ADDRESSES:
                transaction = await fetch_last_spl_transactions(session, address, last_signature[address])
                if transaction:
                    new_transactions.append(transaction)
                    last_signature[address] = transaction['signature']
            if new_transactions:
                message = await create_message(session, new_transactions)
                if message:
                    image_path = get_random_image_path(IMAGE_DIRECTORY)
                    await send_telegram_message(bot, CHAT_ID, message, image_path)

if __name__ == "__main__":
    asyncio.run(main())

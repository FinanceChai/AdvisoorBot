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
    images = [os.path.join(image_directory, file) for file in os.listdir(image_directory) if file.endswith(('.png', '.jpg', '.jpeg'))]
    return random.choice(images) if images else None

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

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/meta?tokenAddress={safely_quote(token_address)}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data and 'data' in data:
                token_info = data['data']
                return {
                    'symbol': token_info.get('tokenSymbol', 'Unknown'),
                    'name': token_info.get('tokenName', 'Unknown'),
                    'market_cap': token_info.get('marketCapFD', 'Unknown'),
                    'mint_address': token_info.get('mintAddress', 'Unknown')
                }
        return {'symbol': 'Unknown', 'name': 'Unknown', 'market_cap': 'Unknown', 'mint_address': 'Unknown'}


async def fetch_last_spl_transactions(session, address, last_signature):
    params = {'account': address, 'limit': 1, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('data') and data['data'][0]['signature'] != last_signature:
                transaction = data['data'][0]
                if 'address' in transaction:  # Check if 'mintAddress' key exists
                    return transaction
                else:
                    print("No mintAddress found in transaction data:", transaction)
                    return None  # Handle missing 'mintAddress'
    return None

async def create_message(session, transactions):
    message_lines = ["🎱 New Transactions 🎱\n\n"]
    for transaction in transactions:
        if transaction:
            token_metadata = await fetch_token_metadata(session, transaction['address'])
            token_symbol = token_metadata['symbol']
            token_name = token_metadata['name']
            market_cap = token_metadata['market_cap']

            if token_symbol not in EXCLUDED_SYMBOLS:
                token_address = transaction.get('address', 'Unknown')
                owner_address = transaction.get('owner', 'Unknown')

                # Check if market_cap is a string and convert it to float for formatting
                try:
                    market_cap_value = float(market_cap)
                    formatted_market_cap = f"${market_cap_value:,.2f}"
                except ValueError:
                    formatted_market_cap = "Unknown"  # Handle cases where conversion fails

                message_lines.append(
                    f"Token Name: {token_name}\n"
                    f"Token Symbol: {token_symbol}\n"
                    f"Fully Diluted Market Cap: {formatted_market_cap}\n"
                    f"<a href='https://solscan.io/token/{safely_quote(token_address)}'>Token Contract</a>\n"
                    f"<a href='https://solscan.io/account/{safely_quote(owner_address)}'>Owner Wallet</a>\n\n"
                )
    return '\n'.join(message_lines) if len(message_lines) > 1 else None



async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signature = {address: None for address in TARGET_ADDRESSES}
    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(60)  # Continuous monitoring every minute
            for address in TARGET_ADDRESSES:
                transaction = await fetch_last_spl_transactions(session, address, last_signature[address])
                if transaction:
                    last_signature[address] = transaction['signature']
                    new_transactions = [transaction]
                    message = await create_message(session, new_transactions)
                    if message:
                        image_path = get_random_image_path(IMAGE_DIRECTORY)
                        await send_telegram_message(bot, CHAT_ID, message, image_path)

if __name__ == "__main__":
    asyncio.run(main())

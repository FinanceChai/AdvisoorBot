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

async def fetch_market_cap(session, token_address):
    # Construct the URL with query parameters for limit and offset
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}?limit=10&offset=0"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
                        
            # Extract the fully diluted market cap (marketCapFD) directly
            market_cap_fd = data.get('marketCapFD', None)
            token_name = data.get('tokenName', 'Unknown')
            token_symbol = data.get('tokenSymbol', 'Unknown')
            
            if market_cap_fd is not None:
                # Format the market cap as a number
                formatted_market_cap = f"${market_cap_fd:,.2f}"
                print(f"Token Name: {token_name}")
                print(f"Token Symbol: {token_symbol}")
                print(f"Fully Diluted Market Cap: {formatted_market_cap}")
            else:
                print("Market cap data is missing or invalid.")
        else:
            response_text = await response.text()
            print(f"Failed to fetch data. Status code: {response.status}, Response: {response_text}")

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
        if transaction:
            # Fetch market cap data using fetch_market_cap function
            token_address = transaction.get('address', 'Unknown')
            token_name, token_symbol, formatted_market_cap = await fetch_market_cap(session, token_address)

            if token_symbol not in EXCLUDED_SYMBOLS:
                owner_address = transaction.get('owner', 'Unknown')

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

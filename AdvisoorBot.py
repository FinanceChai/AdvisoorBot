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
    """Returns a random image path from the specified directory, creating the directory if it does not exist."""
    if not os.path.exists(image_directory):
        os.makedirs(image_directory, exist_ok=True)
        return None  # Return None if the directory was just created and is empty
    
    images = [os.path.join(image_directory, file) for file in os.listdir(image_directory) if file.endswith(('.png', '.jpg', '.jpeg'))]
    if images:
        return random.choice(images)
    else:
        return None

async def send_telegram_message(bot, chat_id, text, image_path=None):
    """Sends a message to a Telegram chat, with an optional resized image. Disables web page preview for text-only messages."""
    if image_path:
        try:
            # Open an image file
            with Image.open(image_path) as img:
                # Resize the image using LANCZOS resampling method
                img = img.resize((200, 200), Image.Resampling.LANCZOS)  # Resize to 800x600 or another dimension as needed
                # Save the resized image to a buffer
                buf = io.BytesIO()
                img_format = 'JPEG' if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg') else 'PNG'
                img.save(buf, format=img_format)
                buf.seek(0)
                # Send photo with caption
                await bot.send_photo(chat_id=chat_id, photo=buf, caption=text, parse_mode='HTML')
        except Exception as e:
            print(f"Error resizing or sending image: {e}")
            # Fallback: send text message if image processing fails
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
    else:
        # Send text only message with disabled web page preview
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # Send initial message for each wallet address
    initial_messages = []
    for address in TARGET_ADDRESSES:
        initial_transactions = await fetch_last_spl_transactions(address, limit=10)
        message = await create_message(initial_transactions)
        initial_messages.append(message)
    await send_telegram_message(bot, CHAT_ID, "\n".join(initial_messages))
    
    last_check_time = datetime.now() - timedelta(minutes=1)
    aggregated_transactions = []

    # Main loop to check for new transactions
    while True:
        current_time = datetime.now()
        if current_time - last_check_time >= timedelta(minutes=1):
            # Aggregate transactions if more than one minute has passed since the last check
            if aggregated_transactions:
                message = await create_message(aggregated_transactions)
                image_path = get_random_image_path(IMAGE_DIRECTORY)
                await send_telegram_message(bot, CHAT_ID, message, image_path)
                aggregated_transactions = []  # Clear aggregated transactions after sending the message
            last_check_time = current_time
        
        for address in TARGET_ADDRESSES:
            new_transactions = await fetch_last_spl_transactions(address, limit=10)
            aggregated_transactions.extend(new_transactions)
        
        await asyncio.sleep(10)  # Check every 10 seconds

async def create_message(transactions):
    """Creates a message from a list of transactions."""
    message_lines = ["🎱 8 Ball Shakes 🎱\n\n"]
    for transaction in transactions:
        symbol = transaction.get('symbol')
        if symbol in excluded_symbols:
            continue
        token_name = transaction.get('tokenName')
        contract_address = transaction.get('tokenAddress')
        wallet_address = transaction.get('owner')
        message_lines.append(
            f"Token Name: {token_name}\n"
            f"Token Symbol: {symbol}\n"
            f"<a href='https://solscan.io/token/{safely_quote(contract_address)}'>CA</a>\n"
            f"<a href='https://solscan.io/account/{safely_quote(wallet_address)}'>Buyer Wallet</a>\n\n"
            f"<a href='https://www.dextools.io/app/en/solana/pair-explorer/{safely_quote(contract_address)}'>View Pair on DexScreener</a>\n"
            f"<a href='https://jup.ag/swap/SOL-{safely_quote(contract_address)}'>Buy on Jupiter</a>\n\n"
        )
    return '\n'.join(message_lines)

async def fetch_last_spl_transactions(address, limit=10):
    """Fetches the last SPL transactions for a given address."""
    transactions = []
    try:
        url = f"https://api.solanabeach.io/token_transfers?address={address}&limit={limit}&sort=desc"
        headers = {"x-api-key": SOLSCAN_API_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for result in data['result']:
                transaction = {
                    'symbol': result.get('symbol'),
                    'tokenName': result.get('tokenName'),
                    'tokenAddress': result.get('tokenAddress'),
                    'owner': result.get('owner')
                }
                transactions.append(transaction)
    except Exception as e:
        print(f"Error fetching transactions for address {address}: {e}")
    return transactions

asyncio.run(main())

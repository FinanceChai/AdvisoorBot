import os
import asyncio
import random
import requests
from telegram import Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv
from urllib.parse import quote as safely_quote  # Import quote function for URL encoding

# Set the event loop policy to prevent issues on Windows environments
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

# Retrieve environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
JUPITER_REFERRAL_KEY = os.getenv('JUPITER_REFERRAL_KEY')
IMAGE_DIRECTORY = os.path.abspath('/root/main/AdvisoorBot/memes')

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signatures = await initialize_signatures(TARGET_ADDRESSES)
    excluded_symbols = {"WSOL", "SOL", "USDC", "WAVAX", "WBTC", "WETH", "ETH"}
    while True:
        for address in TARGET_ADDRESSES:
            new_transactions = await fetch_last_spl_transactions(address, last_signatures)
            for transaction in new_transactions:
                symbol = transaction.get('symbol')
                if symbol in excluded_symbols:
                    continue
                token_name = transaction.get('tokenName')
                amount = transaction.get('changeAmount', '0')
                contract_address = transaction.get('tokenAddress')
                wallet_address = transaction.get('owner')
                signature = transaction.get('signature')
                message = (
                    f"⚠️ Advisoor Transaction ⚠️\n\n"
                    f"Token Name: {token_name}\n"
                    f"Token Symbol: {symbol}\n\n"
                    f"Contract Address: <a href='https://solscan.io/token/{safely_quote(contract_address)}'>{contract_address}</a>\n"
                    f"Wallet Address: <a href='https://solscan.io/account/{safely_quote(wallet_address)}'>{wallet_address}</a>\n"
                    f"Signature: <a href='https://solscan.io/tx/{safely_quote(signature)}'>{signature}</a>\n\n"
                    f"DexScreener: <a href='https://www.dextools.io/app/en/solana/pair-explorer/{safely_quote(contract_address)}'>View Pair</a>\n\n"
                    f"Buy on Jupiter: <a href='https://jup.ag/swap?inputMint=SOL&outputMint={safely_quote(contract_address)}&amount=100000000&slippageBps=50&platformFeeBps=20&referral={JUPITER_REFERRAL_KEY}'>Trade Now</a>\n\n"
                )
                image_path = get_random_image_path(IMAGE_DIRECTORY)
                await send_telegram_message(bot, CHAT_ID, message, image_path)
        await asyncio.sleep(60)  # Check every minute

async def initialize_signatures(addresses):
    """Initialize and return the set of last known signatures."""
    last_signatures = set()
    for address in addresses:
        try:
            params = {'account': address, 'limit': 5, 'offset': 0}
            headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
            url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for transaction in data.get('data', []):
                    signature = transaction.get('signature', '')
                    if isinstance(signature, list):
                        signature = signature[0] if signature else ''
                    if signature:
                        last_signatures.add(signature)
        except requests.RequestException as e:
            print(f"Failed to fetch signatures for {address}: {e}")
    return last_signatures

async def fetch_last_spl_transactions(address, last_signatures):
    """Fetch the latest SPL token transactions for a specific Solana address."""
    new_transactions = []
    try:
        params = {'account': address, 'limit': 5, 'offset': 0}
        headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
        url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for transaction in data.get('data', []):
                signature = transaction.get('signature', '')
                if isinstance(signature, list):
                    signature = signature[0] if signature else ''
                if signature and signature not in last_signatures:
                    new_transactions.append(transaction)
                    last_signatures.add(signature)
    except requests.RequestException as e:
        print(f"Network error when fetching transactions for {address}: {e}")
    return new_transactions

async def send_telegram_message(bot, chat_id, message, image_path):
    """Send a message with inline buttons to a Telegram chat."""
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', disable_web_page_preview=True)
        if image_path:
            with open(image_path, 'rb') as photo:
                await bot.send_photo(chat_id=chat_id, photo=photo)
    except Exception as e:
        print(f"Failed to send message: {e}")

def start(update: Update, context: CallbackContext):
    """Handle the /start command."""
    update.message.reply_text("Welcome to the Advisoor Bot!")

def get_random_image_path(directory):
    """Return a random image path from the specified directory."""
    try:
        images = [file for file in os.listdir(directory) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if images:
            return os.path.join(directory, random.choice(images))
        print("No images found in the directory.")
    except FileNotFoundError:
        print(f"Directory does not exist: {directory}")
    except Exception as e:
        print(f"Error accessing directory: {e}")

def safely_quote(s):
    """Safely quote a string for URL."""

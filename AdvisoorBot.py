import os
import asyncio
import random
import requests
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv

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
    return None

def initialize_signatures(addresses):
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

def fetch_last_spl_transactions(address, last_signatures):
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

async def send_telegram_message(bot, chat_id, transaction):
    """Send a message with inline buttons to a Telegram chat."""
    message_text = (
        f"⚠️ Advisoor Transaction ⚠️\n\n"
        f"Token Name: {transaction['tokenName']}\n"
        f"Token Symbol: {transaction['symbol']}\n\n"
        f"CA: {transaction['tokenAddress']}\n"
        f"Wallet: {transaction['owner']}\n\n"
    )
    keyboard = [
        [InlineKeyboardButton("Copy CA", callback_data=f"CA_{transaction['tokenAddress']}")],
        [InlineKeyboardButton("Copy Wallet", callback_data=f"Wallet_{transaction['owner']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print(f"Failed to send message: {e}")

def button_handler(update: Update, context: CallbackContext):
    """Handle button presses."""
    query = update.callback_query
    query.answer()
    data = query.data
    # Extract the type and address from callback_data
    if data.startswith('CA_'):
        address = data[3:]
        context.bot.send_message(chat_id=query.message.chat_id, text=f"Contract Address: {address}")
    elif data.startswith('Wallet_'):
        address = data[7:]
        context.bot.send_message(chat_id=query.message.chat_id, text=f"Wallet Address: {address}")

def main():
    updater = Updater(token=TELEGRAM_TOKEN)

    # Handler setup
    updater.dispatcher.add_handler(CommandHandler('start', start))  # start function must be defined
    updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))

    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

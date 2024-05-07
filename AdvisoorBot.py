import os
import asyncio
import random
import requests
from telegram import Bot, InputFile
from dotenv import load_dotenv
from urllib.parse import quote as safely_quote

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
    """Sends a message to a Telegram chat, with an optional image."""
    if image_path:
        with open(image_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode='HTML')
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signatures = {address: [] for address in TARGET_ADDRESSES}

    # Fetch the latest trades for each address and initialize the last signatures list
    for address in TARGET_ADDRESSES:
        new_transactions = await fetch_last_spl_transactions(address, [])
        last_signatures[address] = [tx['signature'] for tx in new_transactions]
        await process_transactions(new_transactions, bot)

    # Main loop to check for new transactions
    while True:
        for address in TARGET_ADDRESSES:
            new_transactions = await fetch_last_spl_transactions(address, last_signatures[address])
            last_signatures[address].extend([tx['signature'] for tx in new_transactions])
            await process_transactions(new_transactions, bot)
        await asyncio.sleep(60)  # Check every minute

async def process_transactions(transactions, bot):
    """Processes and sends messages for a list of transactions."""
    for transaction in transactions:
        symbol = transaction.get('symbol')
        if symbol in excluded_symbols:
            continue
        token_name = transaction.get('tokenName')
        contract_address = transaction.get('tokenAddress')
        wallet_address = transaction.get('owner')
        message = (
            f"⚠️ Advisoor Transaction ⚠️\n\n"
            f"Token Name: {token_name}\n"
            f"Token Symbol: {symbol}\n\n"
            f"Contract Address: <a href='https://solscan.io/token/{safely_quote(contract_address)}'>CA</a>\n"
            f"Wallet Address: <a href='https://solscan.io/account/{safely_quote(wallet_address)}'>Wallet</a>\n"
            f"DexScreener: <a href='https://www.dextools.io/app/en/solana/pair-explorer/{safely_quote(contract_address)}'>View Pair</a>\n\n"
            f"Buy on Jupiter: <a href='https://jup.ag/swap?inputMint=SOL&outputMint={safely_quote(contract_address)}&amount=100000000&slippageBps=50&platformFeeBps=20&referral={JUPITER_REFERRAL_KEY}'>Trade Now</a>\n\n"
        )
        image_path = get_random_image_path(IMAGE_DIRECTORY)
        await send_telegram_message(bot, CHAT_ID, message, image_path)

async def fetch_last_spl_transactions(address, known_signatures):
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
                if signature and signature not in known_signatures:
                    new_transactions.append(transaction)
    except requests.RequestException as e:
        print(f"Network error when fetching transactions for {address}: {e}")
    return new_transactions

if __name__ == "__main__":
    asyncio.run(main())

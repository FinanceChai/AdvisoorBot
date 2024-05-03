import os
import asyncio
import random
import requests
from telegram import Bot
from dotenv import load_dotenv
from urllib.parse import quote

# Set the event loop policy to avoid issues on Windows with ProactorEventLoop
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

# Retrieve environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS').split(',')
JUPITER_REFERRAL_KEY = os.getenv('JUPITER_REFERRAL_KEY')
IMAGE_DIRECTORY = 'root/main/AdvisoorBot/memes'

def get_random_image_path(directory):
    """Return a random image path from the specified directory."""
    # Implement logic to get a random image path
    pass  # Placeholder, replace with actual implementation

async def initialize_signatures(bot, addresses):
    last_signatures = set()
    for address in addresses:
        # Fetch initial transactions to populate the signatures set
        params = {
            'account': address,
            'limit': 5,  # Adjust based on how far back you want to look initially
            'offset': 0
        }
        headers = {
            'accept': '*/*',
            'token': SOLSCAN_API_KEY
        }
        url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data:
                for transaction in data['data']:
                    signature = transaction.get('signature', '')
                    if isinstance(signature, list):
                        signature = signature[0] if signature else ''
                    if signature:
                        last_signatures.add(signature)
    return last_signatures

from urllib.parse import quote

def safely_quote(value):
    """Ensure the value is a string and then URL-quote it."""
    if isinstance(value, bytes):
        value = value.decode('utf-8')  # Decode bytes to string if needed
    elif isinstance(value, list):
        value = value[0] if value else ''  # Extra check for list, just in case
    return quote(str(value))  # Convert to string to ensure no type issues

async def fetch_last_spl_transactions(address, last_signatures):
    """Fetch the latest SPL token transactions for a specific Solana address."""
    params = {
        'account': address,
        'limit': 5,  # Adjust based on how many transactions you want to fetch
        'offset': 0
    }
    headers = {
        'accept': '*/*',
        'token': SOLSCAN_API_KEY
    }
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    response = requests.get(url, params=params, headers=headers)
    new_transactions = []
    if response.status_code == 200:
        data = response.json()
        if data and 'data' in data:
            for transaction in data['data']:
                signature = transaction.get('signature', '')
                if isinstance(signature, list):
                    signature = signature[0] if signature else ''
                
                if signature and signature not in last_signatures:
                    new_transactions.append(transaction)
                    last_signatures.add(signature)
    return new_transactions

async def main():
    print(f"TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")
    print(f"CHAT_ID: {CHAT_ID}")
    print(f"SOLSCAN_API_KEY: {SOLSCAN_API_KEY}")
    print(f"TARGET_ADDRESSES: {TARGET_ADDRESSES}")
    print(f"JUPITER_REFERRAL_KEY: {JUPITER_REFERRAL_KEY}")
    
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signatures = await initialize_signatures(bot, TARGET_ADDRESSES)
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
                    [Contract Address](https://solscan.io/token/1HHKuLTxYHVM4XZdLEt2ZVZYQsVXmtYsTF4JAv6wnhA)
                    [Wallet Address](https://solscan.io/account/FgKRR7o92EMnQLuD6XNuKKyyMs5a9K1UbvfP1VfQYhR3)
                    [Signature](https://solscan.io/tx/2k6Y3HsCz9TZu7hCDusWGN4sABQu3MFNeihdmyiMontyDSWAc1oTcmEsErpoogNemVPsPPg3CvnXfjGZTxDMUSfw)
                    [DexScreener](https://www.dextools.io/app/en/solana/pair-explorer/1HHKuLTxYHVM4XZdLEt2ZVZYQsVXmtYsTF4JAv6wnhA)
                    [Buy on Jupiter](https://jup.ag/swap?inputMint=SOL&outputMint=1HHKuLTxYHVM4XZdLEt2ZVZYQsVXmtYsTF4JAv6wnhA&amount=100000000&slippageBps=50&platformFeeBps=20&referral=None)
                )
                image_path = get_random_image_path(IMAGE_DIRECTORY)
                # Assuming this is for demonstration purposes, as the function isn't defined
                print(f"Random image path: {image_path}")
                await send_telegram_message(bot, CHAT_ID, message)
        await asyncio.sleep(60)  # Check every minute

async def send_telegram_message(bot, chat_id, message):
    """Send a message to a Telegram chat."""
    await bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)

if __name__ == "__main__":
    asyncio.run(main())

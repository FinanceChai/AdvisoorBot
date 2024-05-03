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
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
JUPITER_REFERRAL_KEY = os.getenv('JUPITER_REFERRAL_KEY')
IMAGE_DIRECTORY = os.path.abspath('/root/main/AdvisoorBot/memes')

def get_random_image_path(directory):
    """Return a random image path from the specified directory."""
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return None
    images = [file for file in os.listdir(directory) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if images:
        return os.path.join(directory, random.choice(images))
    return None

async def initialize_signatures(bot, addresses):
    last_signatures = set()
    for address in addresses:
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
    return last_signatures

async def fetch_last_spl_transactions(address, last_signatures):
    params = {'account': address, 'limit': 5, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    response = requests.get(url, params=params, headers=headers)
    new_transactions = []
    if response.status_code == 200:
        data = response.json()
        for transaction in data.get('data', []):
            signature = transaction.get('signature', '')
            if isinstance(signature, list):
                signature = signature[0] if signature else ''
            if signature and signature not in last_signatures:
                new_transactions.append(transaction)
                last_signatures.add(signature)
    return new_transactions

async def send_telegram_message(bot, chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', disable_web_page_preview=True)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signatures = await initialize_signatures(bot, TARGET_ADDRESSES)
    excluded_symbols = {"WSOL", "SOL", "USDC", "WAVAX", "WBTC", "WETH", "ETH"}
    while True:
        for address in TARGET_ADDRESSES:
            new_transactions = await fetch_last_spl_transactions(address, last_signatures)
            for transaction in new_transactions:
                if transaction.get('symbol') in excluded_symbols:
                    continue
                message = (
                    f"⚠️ Advisoor Transaction ⚠️\n\n"
                    f"Token Name: {transaction['tokenName']}\n"
                    f"Token Symbol: {transaction['symbol']}\n\n"
                    f"Contract Address: {transaction['tokenAddress']}\n\n"
                    f"Wallet Address: {transaction['owner']}\n\n"
                    f"Signature: {transaction['signature']}\n\n"
                    f"<a href='https://www.dextools.io/app/en/solana/pair-explorer/{transaction['tokenAddress']}'>View on DexScreener</a>\n"
                    f"<a href='https://jup.ag/swap?inputMint=SOL&outputMint={transaction['tokenAddress']}&amount=100000000&slippageBps=50&platformFeeBps=20&referral={JUPITER_REFERRAL_KEY}'>Buy on Jupiter</a>\n"
                )
        await asyncio.sleep(60)  # Run this loop every minute

if __name__ == "__main__":
    asyncio.run(main())

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
IMAGE_DIRECTORY = 'root/main/memes'

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
                    f"Contract Address: <a href='https://solscan.io/token/{safely_quote(contract_address)}'>{contract_address}</a>\n"
                    f"Wallet Address: <a href='https://solscan.io/account/{safely_quote(wallet_address)}'>{wallet_address}</a>\n"
                    f"Signature: <a href='https://solscan.io/tx/{safely_quote(signature)}'>{signature}</a>\n\n"
                    f"DexScreener: <a href='https://www.dextools.io/app/en/solana/pair-explorer/{safely_quote(contract_address)}'>View Pair</a>\n\n"
                    f"Buy on Jupiter: <a href='https://jup.ag/swap?inputMint=SOL&outputMint={safely_quote(contract_address)}&amount=100000000&slippageBps=50&platformFeeBps=20&referral={JUPITER_REFERRAL_KEY}'>Trade Now</a>\n\n"
                )
                image_path = get_random_image_path(IMAGE_DIRECTORY)
                await send_telegram_message(bot, CHAT_ID, message, image_path)
        await asyncio.sleep(60)  # Check every minute

async def send_telegram_message(bot, chat_id, message):
    """Send a message to a Telegram chat."""
    await bot.send_message(chat_id=chat_id, text=message)

async def send_telegram_group_message(bot, chat_id, message):
    """Send a message to a Telegram group."""
    await bot.send_message(chat_id=chat_id, text=message)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)

    # Send a message to the individual chat
    individual_message = "Hello from the bot!"
    await send_telegram_message(bot, CHAT_ID, individual_message)

    # Send a message to the group chat
    group_message = "THIS WORKS"
    await send_telegram_group_message(bot, CHAT_ID, group_message)

if __name__ == "__main__":
    asyncio.run(main())

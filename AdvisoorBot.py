import os
import asyncio
import random
import requests
from telegram import Bot
from dotenv import load_dotenv
from urllib.parse import quote as safely_quote  # Import quote function for URL encoding

# Load environment variables from .env file
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
    excluded_symbols = {"WSOL", "SOL", "USDC", "WAVAX", "WBTC", "WETH", "ETH", "BONK"}
    while True:
        last_signatures = await initialize_signatures(TARGET_ADDRESSES)
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
                    f"Contract Address: <a href='https://solscan.io/token/{safely_quote(contract_address)}'>CA</a>\n"
                    f"Wallet Address: <a href='https://solscan.io/account/{safely_quote(wallet_address)}'>Wallet</a>\n"
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


import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot  # You need to install python-telegram-bot package

# Load environment variables from .env file
load_dotenv()

# API key and other settings
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
IMAGE_DIRECTORY = os.path.abspath('/root/advisoorbot/Memes')
EXCLUDED_SYMBOLS = {"ETH", "SOL", "BTC", "BONK", "WAVAX", "WETH", "WBTC", "Bonk", "bonk"}

async def fetch_spl_transactions(session):
    transactions = []
    for address in TARGET_ADDRESSES:
        url = f"https://pro-api.solscan.io/account/transactions?account={address}"
        headers = {'accept': '*/*', 'Authorization': f"Bearer {SOLSCAN_API_KEY}"}
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                transactions.extend(data.get('data', []))
    return transactions

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}"
    headers = {'accept': '*/*', 'Authorization': f"Bearer {SOLSCAN_API_KEY}"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            token_data = data.get('data', [{}])[0]
            return {
                'name': token_data.get('name', 'Unknown'),
                'symbol': token_data.get('symbol', 'Unknown'),
                'market_cap': token_data.get('marketCapFD', 'Unknown'),
                'price': token_data.get('priceUsdt', 'Unknown')
            }
        else:
            print(f"Failed to fetch token data. Status code: {response.status}")
            return None

async def send_telegram_message(bot, name, symbol, address, market_cap, price):
    text = f"""
[IMAGE]
Token Name: {name}
Token Symbol: {symbol}
Contract Address: {address}
Market Cap: {market_cap}
Price: {price}
"""
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():
    async with aiohttp.ClientSession() as session, Bot(token=TELEGRAM_TOKEN) as bot:
        transactions = await fetch_spl_transactions(session)
        for tx in transactions:
            token_address = tx.get('tokenAddress')
            if token_address:
                token_metadata = await fetch_token_metadata(session, token_address)
                if token_metadata:
                    await send_telegram_message(bot, token_metadata['name'], token_metadata['symbol'],
                                                token_address, token_metadata['market_cap'], token_metadata['price'])

if __name__ == "__main__":
    asyncio.run(main())

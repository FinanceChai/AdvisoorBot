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

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
IMAGE_DIRECTORY = os.path.abspath('/root/advisoorbot/Memes')
EXCLUDED_SYMBOLS = {"ETH", "SOL", "BTC", "BONK", "WAVAX", "WETH", "WBTC", "Bonk", "bonk"}

def get_random_image_path(image_directory):
    if not os.path.exists(image_directory):
        os.makedirs(image_directory, exist_ok=True)
        return None
    images = [os.path.join(image_directory, file) for file in os.listdir(image_directory) if file.endswith(('.png', '.jpg', '.jpeg'))]
    if images:
        return random.choice(images)
    else:
        return None

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

async def fetch_token_metadata(session, token_address):
    """Fetches metadata for a given token address from the Solscan API."""
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}?limit=2"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}

    if not SOLSCAN_API_KEY:
        print("API Key is not set. Please check your .env file or environment variables.")
        return {'market_cap': 'Unknown', 'price_usdt': 'Unknown', 'markets': []}

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'market_cap': data.get('marketCapFD', 'Unknown'),
                    'price_usdt': data.get('priceUsdt', 'Unknown'),
                    'markets': data.get('markets', [])
                }
            else:
                print(f"Failed to fetch data. Status code: {response.status}, Response: {await response.text()}")
                return {'market_cap': 'Unknown', 'price_usdt': 'Unknown', 'markets': []}
    except Exception as e:
        print(f"An error occurred while fetching token metadata: {e}")
        return {'market_cap': 'Unknown', 'price_usdt': 'Unknown', 'markets': []}

async def create_message(session, transactions):
    message_lines = ["🎱 New Transactions 🎱\n\n"]
    for transaction in transactions:
        # Fetch metadata for each token involved in the transaction
        token_metadata = await fetch_token_metadata(session, transaction['tokenAddress'])
        
        # Check if metadata was successfully fetched and proceed to construct the message
        if token_metadata:
            token_name = token_metadata['markets'][0]['base']['name'] if token_metadata['markets'] else 'Unknown'
            token_symbol = token_metadata['markets'][0]['base']['symbol'] if token_metadata['markets'] else 'Unknown'
            market_cap = token_metadata['market_cap']
            price_usdt = token_metadata['price_usdt']

            token_address = transaction.get('tokenAddress', 'Unknown')
            owner_address = transaction.get('owner', 'Unknown')
            amount = transaction.get('amount', 'Unknown')  # Assuming 'amount' is the key for the token amount in the transaction data
            
            # Append transaction details to the message list
            message_lines.append(
                f"Token Name: {token_name}\n"
                f"Token Symbol: {token_symbol}\n"
                f"Market Cap: {market_cap if market_cap != 'Unknown' else 'Data not available'}\n"
                f"Price in USDT: {price_usdt if price_usdt != 'Unknown' else 'Data not available'}\n"
                f"Amount: {amount}\n"
                f"Token Address: <a href='https://solscan.io/token/{safely_quote(token_address)}'>View Token</a>\n"
                f"Owner Address: <a href='https://solscan.io/account/{safely_quote(owner_address)}'>View Owner</a>\n"
            )
        else:
            message_lines.append(f"Failed to fetch metadata for token address: {transaction['tokenAddress']}")
    
    # Combine all message parts into a single message
    return '\n'.join(message_lines) if len(message_lines) > 1 else "No new transactions to display."

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    last_signature = {address: None for address in TARGET_ADDRESSES}
    async with aiohttp.ClientSession() as session:
        # Initial fetch of transactions and update last known signatures
        for address in TARGET_ADDRESSES:
            transaction = await fetch_last_spl_transactions(session, address, last_signature[address])
            if transaction:
                last_signature[address] = transaction['signature']

        # Continuous monitoring of new transactions every minute
        while True:
            await asyncio.sleep(60)  # Wait for a minute before checking new transactions
            new_transactions = []
            for address in TARGET_ADDRESSES:
                transaction = await fetch_last_spl_transactions(session, address, last_signature[address])
                if transaction:
                    new_transactions.append(transaction)
                    last_signature[address] = transaction['signature']
            if new_transactions:
                message = await create_message(session, new_transactions)
                if message:
                    image_path = get_random_image_path(IMAGE_DIRECTORY)
                    await send_telegram_message(bot, CHAT_ID, message, image_path)

if __name__ == "__main__":
    asyncio.run(main())

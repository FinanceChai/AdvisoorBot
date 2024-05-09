import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')

async def fetch_last_token_address(session, address, last_signature):
    params = {'account': address, 'limit': 1, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('data') and data['data'][0]['signature'] != last_signature:
                return data['data'][0]['tokenAddress']
    return None

async def main():
    async with aiohttp.ClientSession() as session:
        last_signature = {address: None for address in TARGET_ADDRESSES}
        while True:
            await asyncio.sleep(60)  # Wait for a minute before checking new transactions
            for address in TARGET_ADDRESSES:
                token_address = await fetch_last_token_address(session, address, last_signature[address])
                if token_address:
                    print(f"Token address acquired by {address}: {token_address}")
                    last_signature[address] = token_address

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')

async def fetch_last_transaction(session, address, last_signature):
    """Fetches the most recent transaction for the given address and checks if it's new compared to the last_signature."""
    params = {'account': address, 'limit': 1, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('data') and data['data'][0]['signature'] != last_signature:
                # Return the signature and token address if the transaction is new
                return data['data'][0]['signature'], data['data'][0]['tokenAddress']
    return None, None

async def main():
    async with aiohttp.ClientSession() as session:
        # Initialize the last known signatures for each target address
        last_signature = {address: None for address in TARGET_ADDRESSES}
        
        # Continuously check for new transactions
        while True:
            await asyncio.sleep(60)  # Check every minute
            for address in TARGET_ADDRESSES:
                new_signature, token_address = await fetch_last_transaction(session, address, last_signature[address])
                if new_signature:
                    print(f"New transaction detected for {address}. Token address: {token_address}")
                    # Update the last known signature to the new one
                    last_signature[address] = new_signature

if __name__ == "__main__":
    asyncio.run(main())

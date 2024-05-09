import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}"
    headers = {'accept': '*/*'}

    # Add API key to headers if available
    if SOLSCAN_API_KEY:
        headers['Authorization'] = f"Bearer {SOLSCAN_API_KEY}"
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            token_data = data.get('data', [{}])[0]  # Assume 'data' is a list and fetch the first item
            name = token_data.get('tokenName', 'Unknown')
            symbol = token_data.get('tokenSymbol', 'Unknown')
            market_cap = token_data.get('marketCapFD', 'Unknown')
            return name, symbol, market_cap
        else:
            print(f"Failed to fetch data. Status code: {response.status}")
        return "Unknown", "Unknown", "Unknown"

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        name, symbol, market_cap = await fetch_token_metadata(session, token_address)
        print(f"Token Name: {name}")
        print(f"Token Symbol: {symbol}")
        print(f"Market Cap: {market_cap}")

if __name__ == "__main__":
    asyncio.run(main())

import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_token_metadata(session, token_address):
    """Fetches metadata for a given token address from the Solscan API."""
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}?limit=2"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {SOLSCAN_API_KEY}'}

    if not SOLSCAN_API_KEY:
        print("API Key is not set. Please check your .env file or environment variables.")
        return None

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # Extract and return the data processing...
                return data  # Adjust according to your data extraction logic
            else:
                print(f"Failed to fetch data. Status code: {response.status}, Response: {await response.text()}")
                return None
    except Exception as e:
        print(f"An error occurred while fetching token metadata: {e}")
        return None


async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        token_data = await fetch_token_metadata(session, token_address)
        if token_data:
            print(f"Token Market Cap: {token_data['market_cap']}")
            print(f"Price in USDT: {token_data['price_usdt']}")
            print(f"24h Volume in USDT: {token_data['volume_usdt']}")
            print(f"24h Price Change: {token_data['price_change_24h']}")
            print(f"Market Cap Rank: {token_data['market_cap_rank']}")
            print("Market Information:")
            for market in token_data['markets_info']:
                print(f"Market Name: {market['name']}, Price: {market['price']}, 24h Volume: {market['volume24h']}, Source: {market['source']}")
        else:
            print("No data available for the specified token.")

if __name__ == "__main__":
    asyncio.run(main())

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
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}

    if not SOLSCAN_API_KEY:
        print("API Key is not set. Please check your .env file or environment variables.")
        return None

    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data  # Returning entire JSON data for further processing in main()
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
            print(f"Token Market Cap: ${float(token_data['market_cap']):,.2f}" if token_data['market_cap'] != 'Unknown' else "Unknown")
            print(f"Price in USDT: {token_data['price_usdt']}")
        if token_data and 'markets' in token_data and len(token_data['markets']) > 0:
            market = token_data['markets'][0]  # Safely access the first market
            base_info = market.get('base', {})
            print(f"Symbol: {base_info.get('symbol', 'Unknown')}")
            print(f"Token Name: {base_info.get('name', 'Unknown')}")
        else:
            print("No market information available or token data is incomplete.")

if __name__ == "__main__":
    asyncio.run(main())

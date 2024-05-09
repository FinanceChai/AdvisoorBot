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

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        token_data = await fetch_token_metadata(session, token_address)
        markets = token_data['markets']

        if markets:
            base_info = markets[0].get('base', {})
            name = base_info.get('name', 'Unknown')
            symbol = base_info.get('symbol', 'Unknown')
            print(f"Token Name: {name}")
            print(f"Symbol: {symbol}")
        else:
            print("No market information available or token data is incomplete.")

        market_cap = token_data['market_cap']
        if market_cap != 'Unknown':
            print(f"Token Market Cap: ${float(market_cap):,.2f}")
        else:
            print("Token Market Cap: Unknown")

        print(f"Price in USDT: {token_data['price_usdt']}")

if __name__ == "__main__":
    asyncio.run(main())

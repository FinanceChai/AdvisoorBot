import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/market/token{token_address}?limit=2"
    headers = {'accept': '*/*'}

    # Add API key to headers if available
    if SOLSCAN_API_KEY:
        headers['Authorization'] = f"Bearer {SOLSCAN_API_KEY}"
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            token_data = data.get('data', [{}])[0]  # Assume 'data' is a list and fetch the first item
            # General token information
            name = token_data.get('name', 'Unknown')
            symbol = token_data.get('symbol', 'Unknown')
            market_cap = token_data.get('marketCapFD', 'Unknown')
            # Market details
            markets_info = []
            if 'markets' in token_data:
                for market in token_data['markets']:
                    market_detail = {
                        "name": market.get('name', 'Unknown'),
                        "price": market.get('price', 'Unknown'),
                        "volume24h": market.get('volume24h', 'Unknown'),
                        "source": market.get('source', 'Unknown')
                    }
                    markets_info.append(market_detail)
            return name, symbol, market_cap, markets_info
        else:
            print(f"Failed to fetch data. Status code: {response.status}")
            return "Unknown", "Unknown", "Unknown", []

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        name, symbol, market_cap, markets_info = await fetch_token_metadata(session, token_address)
        print(f"Token Name: {name}")
        print(f"Token Symbol: {symbol}")
        print(f"Market Cap: {market_cap}")
        for market in markets_info:
            print(f"Market Name: {market['name']}")
            print(f"Price: {market['price']}")
            print(f"24h Volume: {market['volume24h']}")
            print(f"Source: {market['source']}")

if __name__ == "__main__":
    asyncio.run(main())

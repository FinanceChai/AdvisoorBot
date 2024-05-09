import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_token_metadata(session, token_address):
    # Correct the URL by adding a missing slash before the token address
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}?limit=2"
    headers = {'accept': '*/*', 'Authorization': f'Bearer {SOLSCAN_API_KEY}'}

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            # Extract direct fields from the response
            market_cap = data.get('marketCapFD', 'Unknown')
            price_usdt = data.get('priceUsdt', 'Unknown')
            volume_usdt = data.get('volumeUsdt', 'Unknown')
            price_change_24h = data.get('priceChange24h', 'Unknown')
            market_cap_rank = data.get('marketCapRank', 'Unknown')

            # Extract market details
            markets_info = []
            markets = data.get('markets', [])
            for market in markets:
                market_detail = {
                    "name": market.get('name', 'Unknown'),
                    "price": market.get('price', 'Unknown'),
                    "volume24h": market.get('volume24h', 'Unknown'),
                    "source": market.get('source', 'Unknown')
                }
                markets_info.append(market_detail)

            return {
                "market_cap": market_cap,
                "price_usdt": price_usdt,
                "volume_usdt": volume_usdt,
                "price_change_24h": price_change_24h,
                "market_cap_rank": market_cap_rank,
                "markets_info": markets_info
            }
        else:
            print(f"Failed to fetch data. Status code: {response.status}")
            return None

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

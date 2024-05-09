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
                market_cap = data.get('marketCapFD', 'Unknown')
                price_usdt = data.get('priceUsdt', 'Unknown')
                volume_usdt = data.get('volumeUsdt', 'Unknown')
                price_change_24h = data.get('priceChange24h', 'Unknown')
                market_cap_rank = data.get('marketCapRank', 'Unknown')

                # Extract market details and token base details if available
                markets_info = []
                for market in data.get('markets', []):
                    market_detail = {
                        "address": market.get('address', 'Unknown'),
                        "ammId": market.get('ammId', 'Unknown'),
                        "base": {
                            "symbol": market['base'].get('symbol', 'Unknown'),
                            "name": market['base'].get('name', 'Unknown'),
                            "icon": market['base'].get('icon', 'Unknown')
                        }
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
            print(f"24h Volume in USDT: {token_data['volume_usdt']}")
            print(f"24h Price Change: {token_data['price_change_24h']}")
            if token_data['markets_info'][0]:
                print(f"Symbol: {market['base']['symbol']}")
                print(f"Token Name: {market['base']['name']}")
        else:
            print("No data available for the specified token.")

if __name__ == "__main__":
    asyncio.run(main())

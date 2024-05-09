import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/list?mintAddress={safely_quote(token_address)}&limit=1"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data['data']:
                token_info = data['data'][0]
                market_cap = token_info.get('marketCapFD', 'Unknown')
                return {
                    'symbol': token_info.get('tokenSymbol', 'Unknown'),
                    'name': token_info.get('tokenName', 'Unknown'),
                    'market_cap': market_cap
                }
        return {'symbol': 'Unknown', 'name': 'Unknown', 'market_cap': 'Unknown'}

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        name, symbol, market_cap = await fetch_token_metadata(session, token_address)
        print(f"Token Name: {name}")
        print(f"Token Symbol: {symbol}")
        print(f"Market Cap: {market_cap}")

if __name__ == "__main__":
    asyncio.run(main())

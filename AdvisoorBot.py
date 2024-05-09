import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()

SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_market_cap(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/list/{token_address}?limit=10&offset=0"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            market_cap_fd = data.get('marketCapFD', None)
            token_name = data.get('tokenName', 'Unknown')
            token_symbol = data.get('tokenSymbol', 'Unknown')
            
            if market_cap_fd is not None:
                formatted_market_cap = f"${market_cap_fd:,.2f}"
                return token_name, token_symbol, formatted_market_cap
            else:
                print("Market cap data is missing or invalid.")
    return "Unknown", "Unknown", None

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        token_name, token_symbol, market_cap = await fetch_market_cap(session, token_address)
        print(f"Token Name: {token_name}")
        print(f"Token Symbol: {token_symbol}")
        print(f"Market Cap: {market_cap}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

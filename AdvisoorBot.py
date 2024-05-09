import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()

SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_market_cap(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/meta?tokenAddress={token_address}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            price = data.get('price', None)
            token_name = data.get('name', 'Unknown')
            token_symbol = data.get('symbol', 'Unknown')
            decimals = data.get('decimals', None)
            supply = supply.get('supply',None)
            Mkt_Cap = price * supply / decimals
            
            if price is not None:
                formatted_price = f"${mkt_cap:,.2f}"
                return token_name, token_symbol, formatted_price
            else:
                print("Market cap data is missing or invalid.")
    return "Unknown", "Unknown", None

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        token_name, token_symbol, market_cap = await fetch_market_cap(session, token_address)
        print(f"Token Name: {token_name}")
        print(f"Token Symbol: {token_symbol}")
        print(f"Market Cap: {mkt_cap}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

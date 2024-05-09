import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()

SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_market_cap(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/TokenList={token_address}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            price = data.get('priceUst', None)
            token_name = data.get('tokenName', 'Unknown')
            token_symbol = data.get('tokenSymbol', 'Unknown')
            market_cap = data.get('marketCapFD', None)
                        
            print(f"Price: {price}, Type: {type(price)}")
            print(f"Name: {token_name}, Type: {type(token_name)}")
            print(f"Token Symbol: {token_symbol}, Type: {type(token_symbol)}")
            print(f"Market Cap: {market_cap}, Type: {type(market_cap)}")
            
            return token_name, token_symbol, market_cap
        
        print(f"Failed to fetch data. Status code: {response.status}")
        return "Unknown", "Unknown", None

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        data = await fetch_market_cap(session, token_address)
        if data is not None:
            token_name, token_symbol, market_cap = data
            print(f"Token Name: {token_name}")
            print(f"Token Symbol: {token_symbol}")
            print(f"Market Cap: {market_cap}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

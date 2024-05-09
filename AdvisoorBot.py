import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()

SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_market_cap(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/TokenList={token_address}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            price = data.get('priceUst', None)
            token_name = data.get('tokenName', 'Unknown')
            token_symbol = data.get('tokenSymbol', 'Unknown')
            market_cap = data.get('marketCapFD', None)
                        
            print(f"Price: {price}, Type: {type(priceUst)}")
            print(f"Name: {token_name}, Type: {type(tokenName)}")
            print(f"token_symbol: {token_symbol}, Type: {type(tokenSymbol)}")

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token address
    async with aiohttp.ClientSession() as session:
        token_name, token_symbol, market_cap = await fetch_market_cap(session, token_address)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

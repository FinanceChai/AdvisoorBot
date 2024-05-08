import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the necessary API key and details from the environment
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')

async def fetch_market_cap(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/token/meta?tokenAddress={token_address}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            print("Data retrieved from API:", data)  # Debug print the whole API response
            
            if data:
                name = data.get('name', "Unknown")
                symbol = data.get('symbol', "Unknown")
                price = data.get('price', 0)  # Default price is 0 if not available
                supply = data.get('supply', 0)  # Default supply is 0 if not available
                decimals = data.get('decimals', 0)  # Default decimals is 0 if not available

                if price and supply and decimals:
                    adjusted_supply = float(supply) / (10 ** decimals)
                    market_cap = price * adjusted_supply
                    print(f"Token: {name} ({symbol})")
                    print(f"Current Price: ${price}")
                    print(f"Adjusted Circulating Supply: {adjusted_supply}")
                    print(f"Current Market Cap: ${market_cap:,.2f}")
                else:
                    print("Price, supply, or decimals data is missing or invalid.")
            else:
                print("No data found for the specified token address.")
        else:
            response_text = await response.text()
            print(f"Failed to fetch data. Status code: {response.status}, Response: {response_text}")

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    async with aiohttp.ClientSession() as session:
        await fetch_market_cap(session, token_address)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the necessary API key and details from the environment
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')

async def fetch_market_cap(session, mint_address):
    url = f"https://pro-api.solscan.io/v1.0/token/list?mintAddress={mint_address}&limit=1"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            print("Data retrieved from API:", data)  # Debug print the whole API response
            
            if data['data'] and len(data['data']) > 0:
                token_info = data['data'][0]
                current_price = token_info.get('priceUst', None)
                supply_info = token_info.get('supply', None)

                circulating_supply = None
                if supply_info:
                    circulating_supply = supply_info.get('uiAmount', None)
                
                print("Current Price:", current_price)
                print("Circulating Supply:", circulating_supply)

                if current_price is not None and circulating_supply is not None:
                    market_cap = current_price * circulating_supply
                    print(f"Current Market Cap for {mint_address}: ${market_cap:,.2f}")
                else:
                    print("Critical data for market cap calculation is missing.")
            else:
                print("No data found for the specified mint address.")
        else:
            print(f"Failed to fetch data. Status code: {response.status}, Response: {response.text}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <mint_address>")
        return
    mint_address = sys.argv[1]
    async with aiohttp.ClientSession() as session:
        await fetch_market_cap(session, mint_address)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the necessary API key and details from the environment
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')

async def fetch_market_cap(session, mint_address):
    # Define the URL with the mint address to fetch the token's data
    url = f"https://pro-api.solscan.io/v1.0/token/list?mintAddress={mint_address}&limit=1"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    # Perform the HTTP GET request
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data['data']:
                token_info = data['data'][0]
                current_price = token_info.get('priceUst', 0)
                supply_info = token_info.get('supply', {})
                circulating_supply = supply_info.get('uiAmount', 0)  # uiAmount should be used as it represents the user-friendly amount.

                # Calculate market cap
                if current_price and circulating_supply:
                    market_cap = current_price * circulating_supply
                    print(f"Current Market Cap for {mint_address}: ${market_cap:,.2f}")
                else:
                    print("Price or circulating supply data is missing.")
            else:
                print("No data found for the specified mint address.")
        else:
            print(f"Failed to fetch data. Status code: {response.status}")

async def main():
    # Define the mint address for the token whose market cap you want to fetch
    mint_address = "Enter_Your_Token_Mint_Address_Here"
    
    # Create a session to manage HTTP requests
    async with aiohttp.ClientSession() as session:
        await fetch_market_cap(session, mint_address)

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())

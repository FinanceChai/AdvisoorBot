import asyncio
import aiohttp
import os
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
                current_price = token_info.get('priceUst', None)  # Check for current price
                supply_info = token_info.get('supply', {})  # This assumes there is a 'supply' key

                # Initialize circulating supply to handle cases where it might not be provided
                circulating_supply = supply_info.get('uiAmount', None) if supply_info else None

                print("Current Price:", current_price)  # Debug print the price
                print("Circulating Supply:", circulating_supply)  # Debug print the circulating supply

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
    mint_address = "Enter_Your_Token_Mint_Address_Here"
    async with aiohttp.ClientSession() as session:
        await fetch_market_cap(session, mint_address)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
from dotenv import load_dotenv
import os

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
                market_cap = token_info.get('marketCapFD', 'Unknown')
                print(f"Market Cap for {mint_address}: ${market_cap:,.2f}")
            else:
                print("No data found for the specified mint address.")
        else:
            print(f"Failed to fetch data. Status code: {response.status}")

async def main():
    # Define the mint address for the token whose market cap you want to fetch
    mint_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    
    # Create a session to manage HTTP requests
    async with aiohttp.ClientSession() as session:
        await fetch_market_cap(session, mint_address)

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())

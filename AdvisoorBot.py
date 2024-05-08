import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the necessary API key and details from the environment
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')

async def fetch_market_cap(session, token_address):
    # Construct the URL with query parameters for limit and offset
    url = f"https://pro-api.solscan.io/v1.0/market/token/{token_address}?limit=10&offset=0"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            print("Data retrieved from API:", data)  # Debug print the whole API response
            
            # Extract the fully diluted market cap (marketCapFD) directly
            market_cap_fd = data.get('marketCapFD', None)
            
            if market_cap_fd is not None:
                # Format the market cap as a number
                print(f"Fully Diluted Market Cap: ${market_cap_fd:,.2f}")
            else:
                print("Market cap data is missing or invalid.")
        else:
            response_text = await response.text()
            print(f"Failed to fetch data. Status code: {response.status}, Response: {response_text}")

async def main():
    token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    async with aiohttp.ClientSession() as session:
        await fetch_market_cap(session, token_address)

if __name__ == "__main__":
    asyncio.run(main())

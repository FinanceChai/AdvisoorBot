import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

async def fetch_token_metadata(session, contract_address):
    url = f"https://pro-api.solscan.io/v1.0/token/list?mintAddress={contract_address}&limit=1"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data['data']:
                return data['data'][0]  # Return the token data for the specified contract address
        return None

async def main():
    contract_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example contract address
    async with aiohttp.ClientSession() as session:
        token_data = await fetch_token_metadata(session, contract_address)
        if token_data:
            print("Token Data:", token_data)
        else:
            print("Token not found.")

if __name__ == "__main__":
    asyncio.run(main())

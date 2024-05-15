import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Bot
from urllib.parse import quote as safely_quote

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
EXCLUDED_SYMBOLS = {"ETH", "BTC", "BONK", "Bonk"}  # Add or modify as necessary

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/market/token/{safely_quote(token_address)}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            # Check if 'markets' data is available and has entries
            if 'markets' in data and data['markets']:
                market = data['markets'][0]  # Assuming you want the first market listed

                # Parse the needed data from the first market entry
                result = {
                    'mint_address': market.get('base', {}).get('address'),
                    'token_symbol': market.get('base', {}).get('symbol'),
                    'token_name': market.get('base', {}).get('name'),
                    'decimals': market.get('base', {}).get('decimals'),
                    'icon_url': market.get('base', {}).get('icon'),
                    'website': None,  # Update if API provides this information
                    'twitter': None,  # Update if API provides this information
                    'market_cap_rank': None,  # Update if API provides this information
                    'price_usdt': market.get('price'),  # Assuming 'price' is equivalent to 'price_usdt'
                    'market_cap_fd': market.get('market_cap_fd'),  # Use the fetched value
                    'volume': market.get('volume24h'),  # Assuming 'volume24h' is what you need
                    'coingecko_info': None,  # Update if API provides this information
                    'tag': None  # Update if API provides this information
                }

                return result
            else:
                print(f"No market data available for token: {token_address}")
        else:
            print(f"Failed to fetch metadata, status code: {response.status}")
    return None

async def send_telegram_message(bot, chat_id, text):
    await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)

async def fetch_last_spl_transactions(session, address, last_signature):
    params = {'account': address, 'limit': 1, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('data') and data['data'][0]['signature'] != last_signature:
                transaction_data = data['data'][0]
                return {
                    'signature': transaction_data['signature'],
                    'token_address': transaction_data['tokenAddress'],
                    'owner_address': transaction_data['owner'],  # Assuming 'owner' is the key for owner address
                    'source_token': transaction_data.get('sourceToken', 'Unknown'),  # Assuming 'sourceToken' indicates SOL or WSOL
                    'ticker': transaction_data.get('symbol', 'Unknown')  # Assuming 'symbol' is the key for the ticker
                }
    return None

async def create_message(session, transactions):
    message_lines = ["📝 Advisoor Trade 🔮\n"]
    for transaction in transactions:
        # Fetch metadata for each transaction's token address
        token_metadata = await fetch_token_metadata(session, transaction['token_address'])
        
        # Debugging: Print the fetched metadata
        print(f"Fetched Metadata for {transaction['token_address']}: {token_metadata}")
        
        # Check if metadata was successfully fetched
        if not token_metadata:
            message_lines.append(f"Failed to fetch ca {transaction['token_address']}. Maybe be a future launch!?\n")
            continue
        
        # Extract token details with default values if keys are missing
        token_symbol = token_metadata.get('token_symbol', 'Unknown')
        token_name = token_metadata.get('token_name', 'Unknown')
        ticker = transaction['ticker']  # Use the ticker directly from the transaction data

        # Skip adding details for excluded symbols
        if token_symbol in EXCLUDED_SYMBOLS:
            print(f"Skipping excluded symbol: {token_symbol}")  # Debugging line
            continue
             
        # Append token details to message lines
        message_lines.append(
            f"Ticker: {ticker}\n"
            f"<a href='https://solscan.io/token/{safely_quote(transaction['token_address'])}'>Contract Address</a>\n"
            f"<a href='https://solscan.io/account/{safely_quote(transaction['owner_address'])}'>Owner Wallet</a>\n"
            f"<a href='https://dexscreener.com/search?q={safely_quote(transaction['token_address'])}'>DexScreener</a>\n\n"
            f"<a href='https://t.me/solana_trojanbot?start=r-0xrubberd319503'>🔥 Trade with Trojan Bot 🔥</a>\n"
        )
        
        # Add Twitter link if available
        twitter_handle = token_metadata.get('twitter')
        if twitter_handle:
            message_lines.append(f"<a href='https://twitter.com/{safely_quote(twitter_handle)}'>Twitter</a>\n")

    # Debugging: Print final message before returning
    final_message = '\n'.join(message_lines)
    print(f"Final Message: {final_message}")
    
    return final_message if len(message_lines) > 1 else None

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    async with aiohttp.ClientSession() as session:
        last_signature = {address: None for address in TARGET_ADDRESSES}
        for address in TARGET_ADDRESSES:
            transaction_details = await fetch_last_spl_transactions(session, address, None)
            if transaction_details:
                last_signature[address] = transaction_details['signature']

        while True:
            await asyncio.sleep(60)
            for address in TARGET_ADDRESSES:
                transaction_details = await fetch_last_spl_transactions(session, address, last_signature[address])
                if transaction_details:
                    new_signature = transaction_details['signature']
                    transactions = [transaction_details]  # List expected by create_message
                    message = await create_message(session, transactions)
                    if message:
                        await send_telegram_message(bot, CHAT_ID, message)
                    last_signature[address] = new_signature

if __name__ == "__main__":
    asyncio.run(main())

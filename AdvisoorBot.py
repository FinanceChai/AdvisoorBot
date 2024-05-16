import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote as safely_quote
from telegram.ext import ApplicationBuilder, CommandHandler

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
EXCLUDED_SYMBOLS = {"ETH", "BTC", "BONK", "Bonk"}  # Add or modify as necessary

application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/market/token/{safely_quote(token_address)}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if 'markets' in data and data['markets']:
                market = data['markets'][0]  # Assuming you want the first market listed

                result = {
                    'mint_address': market.get('base', {}).get('address'),
                    'token_symbol': market.get('base', {}).get('symbol'),
                    'token_name': market.get('base', {}).get('name'),
                    'decimals': market.get('base', {}).get('decimals'),
                    'icon_url': market.get('base', {}).get('icon'),
                    'website': None,
                    'twitter': None,
                    'market_cap_rank': None,
                    'price_usdt': market.get('price'),
                    'market_cap_fd': market.get('market_cap_fd'),
                    'volume': market.get('volume24h'),
                    'coingecko_info': None,
                    'tag': None
                }

                return result
            else:
                print(f"No market data available for token: {token_address}")
        else:
            print(f"Failed to fetch metadata, status code: {response.status}")
    return None

async def send_telegram_message(bot, chat_id, text, reply_markup):
    await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True, reply_markup=reply_markup)

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
                    'owner_address': transaction_data['owner'],
                    'source_token': transaction_data.get('sourceToken', 'Unknown'),
                    'ticker': transaction_data.get('symbol', 'Unknown')
                }
    return None

async def create_message(session, transactions):
    message_lines = ["📝 Advisoor Trade 🔮\n"]
    for transaction in transactions:
        token_metadata = await fetch_token_metadata(session, transaction['token_address'])
        
        print(f"Fetched Metadata for {transaction['token_address']}: {token_metadata}")
        
        if not token_metadata:
            message_lines.append(
                f"LP Sniping Opportunity 🔫"
                f"<a href='https://solscan.io/token/{safely_quote(transaction['token_address'])}'>Go to Contract Address</a>\n"
            )
            continue
        
        token_symbol = token_metadata.get('token_symbol', 'Unknown')
        token_name = token_metadata.get('token_name', 'Unknown')
        ticker = transaction['ticker']

        if token_symbol in EXCLUDED_SYMBOLS:
            print(f"Skipping excluded symbol: {token_symbol}")
            continue
        
        last_five_chars_owner = transaction['owner_address'][-5:]
        last_five_chars_token = transaction['token_address'][-5:]

        
        message_lines.append(
            f"Ticker: {ticker}\n"
            f"<a href='https://solscan.io/token/{safely_quote(transaction['token_address'])}'>Contract Address</a> -{last_five_chars_token}\n"
            f"<a href='https://solscan.io/account/{safely_quote(transaction['owner_address'])}'>Owner Wallet</a> -{last_five_chars_owner}\n"
            f"<a href='https://dexscreener.com/search?q={safely_quote(transaction['token_address'])}'>DexScreener</a>\n"
            f"<a href='https://rugcheck.xyz/tokens/{safely_quote(transaction['token_address'])}'>RugCheck</a>\n\n"
        )
        
        twitter_handle = token_metadata.get('twitter')
        if twitter_handle:
            message_lines.append(f"<a href='https://twitter.com/{safely_quote(twitter_handle)}'>Twitter</a>\n")

    final_message = '\n'.join(message_lines)
    print(f"Final Message: {final_message}")

    if len(message_lines) > 1:
        keyboard = [
            [InlineKeyboardButton("Trojan", url="https://t.me/solana_trojanbot?start=r-0xrubberd319503"),
             InlineKeyboardButton("Photon", url="https://example.com/photon")],
            [InlineKeyboardButton("Bonkbot", url="https://example.com/bonkbot"),
             InlineKeyboardButton("BananaGun", url="https://example.com/bananagun")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        return final_message, reply_markup
    else:
        return None, None

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
                    transactions = [transaction_details]
                    message, reply_markup = await create_message(session, transactions)
                    if message:
                        await send_telegram_message(bot, CHAT_ID, message, reply_markup)
                    last_signature[address] = new_signature

if __name__ == "__main__":
    asyncio.run(main())

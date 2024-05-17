import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, Update
from urllib.parse import quote as safely_quote
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
EXCLUDED_SYMBOLS = {"ETH", "BTC", "BONK", "Bonk"}  # Add or modify as necessary

application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def fetch_token_metadata(session, token_address):
    url = f"https://pro-api.solscan.io/v1.0/account/{safely_quote(token_address)}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if 'metadata' in data and 'data' in data['metadata']:
                    metadata = data['metadata']['data']
                    result = {
                        'mint_address': token_address,
                        'token_symbol': metadata.get('symbol', 'Unknown'),
                        'token_name': metadata.get('name', 'Unknown'),
                        'decimals': data.get('tokenInfo', {}).get('decimals'),
                        'icon_url': metadata.get('image'),
                        'website': metadata.get('website'),
                        'twitter': metadata.get('twitter'),
                        'telegram': metadata.get('telegram'),
                        'market_cap_rank': None,
                        'price_usdt': None,
                        'market_cap_fd': None,
                        'volume': None,
                        'coingecko_info': None,
                        'tag': None
                    }
                    return result
                else:
                    print(f"Error: No metadata available for token: {token_address}")
            else:
                print(f"Error: Failed to fetch metadata, status code: {response.status}")
    except Exception as e:
        print(f"Error: Exception occurred while fetching metadata for token {token_address} - {e}")
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
    buttons = []

    for transaction in transactions:
        token_metadata = await fetch_token_metadata(session, transaction['token_address'])

        if token_metadata:
            print(f"Fetched Metadata for {transaction['token_address']}: {token_metadata}")
        else:
            print(f"Error: Metadata for {transaction['token_address']} could not be retrieved")

        if not token_metadata:
            message_lines.append(
                f"🔫 LP Sniping Opportunity 🔫\n\n"
                f"<a href='https://solscan.io/token/{safely_quote(transaction['token_address'])}'>Go to Contract Address</a>\n"
                f"<a href='https://rugcheck.xyz/tokens/{safely_quote(transaction['token_address'])}'>RugCheck</a>\n\n"
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
            f"<a href='https://solscan.io/token/{safely_quote(transaction['token_address'])}'>Solscan - Token</a> (-{last_five_chars_token})\n"
            f"<a href='https://solscan.io/account/{safely_quote(transaction['owner_address'])}'>Solscan - Buyer Wallet</a> (-{last_five_chars_owner})\n\n"
            f"<a href='https://dexscreener.com/search?q={safely_quote(transaction['token_address'])}'>DexScreener🔍 | </a>"
            f"<a href='https://rugcheck.xyz/tokens/{safely_quote(transaction['token_address'])}'>RugCheck✅</a>\n"
        )

        if token_metadata.get('website'):
            message_lines.append(f"🌐 Website: <a href='{token_metadata['website']}'>{token_metadata['website']}</a>\n")
        if token_metadata.get('twitter'):
            twitter_username = token_metadata['twitter'].rstrip('/').split('/')[-1]
            message_lines.append(f"🐦 Twitter: <a href='{token_metadata['twitter']}'>{twitter_username}</a>\n")
            message_lines.append(f"✒️ TweetScout: <a href='https://app.tweetscout.io/search?q={twitter_username}'>Check Score</a>\n")
        if token_metadata.get('telegram'):
            message_lines.append(f"✉️ Telegram: <a href='{token_metadata['telegram']}'>{token_metadata['telegram']}</a>\n")

        buttons.append([InlineKeyboardButton("Copy CA", callback_data=f"copy_{transaction['token_address']}")])
        buttons.append([InlineKeyboardButton("Copy Buyer Address", callback_data=f"copy_{transaction['owner_address']}")])

    final_message = '\n'.join(message_lines)
    print(f"Final Message: {final_message}")

    if len(message_lines) > 1:
        reply_markup = InlineKeyboardMarkup(buttons)
        return final_message, reply_markup
    else:
        return None, None

async def handle_copy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Address copied!", show_alert=True)
    address_type, address = query.data.split('_')[0], query.data.split('_')[1]
    address_type_text = "Contract Address" if address_type == "copy" else "Buyer Address"
    await query.message.reply_text(f"{address_type_text}: <code>{address}</code>", parse_mode='HTML')

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
    application.add_handler(CallbackQueryHandler(handle_copy))
    application.run_polling()

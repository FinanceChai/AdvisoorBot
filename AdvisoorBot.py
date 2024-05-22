import os
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote as safely_quote
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
EXCLUDED_SYMBOLS = {"ETH", "BTC", "BONK", "Bonk"}  # Add or modify as necessary

application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def fetch_token_metadata(session, token_address):
    logger.info(f"Fetching token metadata for: {token_address}")
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    timestamp_now = int(now.timestamp())
    timestamp_one_hour_ago = int(one_hour_ago.timestamp())

    url = f"https://pro-api.solscan.io/v1.0/market/token/{safely_quote(token_address)}?limit=10&offset=0&startTime={timestamp_one_hour_ago}&endTime={timestamp_now}"
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if 'markets' in data and data['markets']:
                    market = data['markets'][0]  # Assuming you want the first market listed

                    result = {
                        'token_symbol': market.get('base', {}).get('symbol'),
                        'token_name': market.get('base', {}).get('name'),
                        'decimals': market.get('base', {}).get('decimals'),
                        'icon_url': market.get('base', {}).get('icon'),
                        'price_usdt': data.get('priceUsdt'),
                        'volume_usdt': sum(market.get('volume24h', 0) for market in data['markets'] if market.get('volume24h') is not None),  # Calculate the total volume over the last hour
                        'market_cap_fd': data.get('marketCapFD'),
                        'total_liquidity': sum(market.get('liquidity', 0) for market in data['markets'] if market.get('liquidity') is not None),  # Calculate the total liquidity
                        'price_change_24h': data.get('priceChange24h')
                    }

                    logger.info(f"Token metadata fetched: {result}")
                    return result
                else:
                    logger.info(f"No market data available for token: {token_address}")
            else:
                logger.error(f"Failed to fetch metadata, status code: {response.status}")
    except Exception as e:
        logger.error(f"Exception occurred while fetching metadata for token {token_address} - {e}")
    return None

async def create_message(session, token_address):
    logger.info("Creating message for transactions")
    message_lines = ["📝 Token Information 🔮\n"]
    token_metadata = await fetch_token_metadata(session, token_address)
    
    if not token_metadata:
        message_lines.append(
            f"🔫 No data available for the provided token address 🔫\n\n"
            f"<a href='https://solscan.io/token/{safely_quote(token_address)}'>Go to Contract Address</a>\n"
        )
    else:
        token_symbol = token_metadata.get('token_symbol', 'Unknown')
        token_name = token_metadata.get('token_name', 'Unknown')
        price_usdt = token_metadata.get('price_usdt', 'N/A')
        volume_usdt = "${:,.0f}".format(token_metadata.get('volume_usdt', 0))
        market_cap_fd = "${:,.0f}".format(token_metadata.get('market_cap_fd', 0))
        total_liquidity = "${:,.0f}".format(token_metadata.get('total_liquidity', 0))

        if price_usdt != 'N/A' and token_metadata.get('price_change_24h') is not None:
            price_usdt = float(price_usdt)
            price_change_24h = token_metadata.get('price_change_24h')
            price_change_ratio = price_change_24h / (price_usdt - price_change_24h)
            price_change_24h_str = "{:.2f}%".format(price_change_ratio * 100)
        else:
            price_change_24h_str = "N/A"

        total_volume = token_metadata.get('volume_usdt', 0)
        market_cap = token_metadata.get('market_cap_fd', 1)
        volume_market_cap_ratio = total_volume / market_cap
        volume_market_cap_ratio_str = "{:.2f}x".format(volume_market_cap_ratio)

        liquidity_market_cap_ratio = (token_metadata.get('total_liquidity', 0) / market_cap) * 100
        liquidity_market_cap_ratio_str = "{:.2f}%".format(liquidity_market_cap_ratio)

        message_lines.append(
            f"Token Name: {token_name}\n\n"
            f"<b><u>Token Overview</u></b>\n"
            f"🔣 Token Symbol: {token_symbol}\n"
            f"📈 Price (USDT): ${price_usdt}\n"
            f"⛽ Volume (USDT): {volume_usdt}\n"
            f"🌛 Market Cap (FD): {market_cap_fd}\n"
            f"💧 Total Liquidity: {total_liquidity}\n"
            f"🔍 Liquidity / Market Cap: {liquidity_market_cap_ratio_str}\n\n"
            f"<b><u>Recent Market Activity</u></b>\n"
            f"💹 Price Change (24h): {price_change_24h_str}\n"
            f"📊 Total Volume (1h): ${total_volume:,.0f}\n"
            f"🔍 Volume / Market Cap: {volume_market_cap_ratio_str}\n\n"
            f"<b><u>Risk Management</u></b>\n"
            f"<a href='https://solscan.io/token/{safely_quote(token_address)}'>Go to Contract Address</a>\n"
            f"<a href='https://rugcheck.xyz/tokens/{safely_quote(token_address)}'>RugCheck</a>\n"
        )
    
    final_message = '\n'.join(message_lines)

    if len(message_lines) > 1:
        keyboard = [
            [InlineKeyboardButton("Photon 💡", url="https://photon-sol.tinyastro.io/@rubberd"),
             InlineKeyboardButton("Pepeboost 🐸", url="https://t.me/pepeboost_sol07_bot?start=ref_01inkp"),
             InlineKeyboardButton("🤵🏼🥸 Advisoor Scan 🥸🤵🏼", url="https://t.me/ManjusriBot")]
        ]
        return final_message, InlineKeyboardMarkup(keyboard)
    else:
        return final_message, None

async def handle_token_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /search [contract address]")
        return

    token_address = context.args[0]
    async with aiohttp.ClientSession() as session:
        message, reply_markup = await create_message(session, token_address)
        if message:
            await send_telegram_message(Bot(token=TELEGRAM_TOKEN), CHAT_ID, message, reply_markup)
        else:
            await update.message.reply_text("Failed to retrieve token information.")

async def send_telegram_message(bot, chat_id, text, reply_markup):
    await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True, reply_markup=reply_markup)

def main():
    application.add_handler(CommandHandler("search", handle_token_info))
    application.run_polling()

if __name__ == "__main__":
    main()

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Get the API key from the environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SOLSCAN_API_KEY = os.getenv('SOLSCAN_API_KEY')
TARGET_ADDRESSES = os.getenv('TARGET_ADDRESS', '').split(',')
IMAGE_DIRECTORY = os.path.abspath('/root/advisoorbot/Memes')
EXCLUDED_SYMBOLS = {"ETH", "SOL", "BTC", "BONK"}  # Add or modify as necessary

def get_random_image_path(image_directory):
    if not os.path.exists(image_directory):
        os.makedirs(image_directory, exist_ok=True)
        return None
    images = [os.path.join(image_directory, file) for file in os.listdir(image_directory) if file.endswith(('.png', '.jpg', '.jpeg'))]
    if images:
        return random.choice(images)
    else:
        return None
        
async def send_telegram_message(bot, chat_id, text, image_path=None):
    if image_path:
        try:
            with Image.open(image_path) as img:
                img = img.resize((200, 200), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img_format = 'JPEG' if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg') else 'PNG'
                img.save(buf, format=img_format)
                buf.seek(0)
                await bot.send_photo(chat_id, photo=buf, caption=text, parse_mode='HTML')
        except Exception as e:
            print(f"Error resizing or sending image: {e}")
            await bot.send_message(chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
    else:
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
                    'owner_address': transaction_data['owner']  # Assuming 'owner' is the key for owner address
                }
    return None

async def create_message(session, transactions):
    message_lines = ["🎱 New Transactions 🎱\n\n"]
    for transaction in transactions:
        token_metadata = await fetch_token_metadata(session, transaction['token_address'])
        token_symbol = token_metadata.get('symbol', 'Unknown') if token_metadata else 'Unknown'
        if token_symbol in EXCLUDED_SYMBOLS:
            continue
        token_name = token_metadata.get('name', 'Unknown') if token_metadata else 'Unknown'
        message_lines.append(
            f"Token Name: {token_name}\n"
            f"Token Symbol: {token_symbol}\n"
            f"<a href='https://solscan.io/token/{safely_quote(transaction['token_address'])}'>Token Contract</a>\n"
            f"<a href='https://solscan.io/account/{safely_quote(transaction['owner_address'])}'>Owner Wallet</a>\n\n"
        )
    return '\n'.join(message_lines) if len(message_lines) > 1 else None

async def main():
    async with aiohttp.ClientSession() as session:
        # Initialize the last known signatures for each target address
        last_signature = {address: None for address in TARGET_ADDRESSES}
        
        # Populate the initial last known signatures to prevent the first transaction from repeating
        for address in TARGET_ADDRESSES:
            transaction_details = await fetch_last_spl_transactions(session, address, None)
            if transaction_details:
                last_signature[address] = transaction_details['signature']
        
        # Continuously check for new transactions
        while True:
            await asyncio.sleep(60)  # Check every minute
            for address in TARGET_ADDRESSES:
                transaction_details = await fetch_last_spl_transactions(session, address, last_signature[address])
                if transaction_details:
                    new_signature = transaction_details['signature']
                    token_address = transaction_details['token_address']
                    print(f"New transaction detected for {address}. Token address: {token_address}")
                    # Update the last known signature to the new one
                    last_signature[address] = new_signature

if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())

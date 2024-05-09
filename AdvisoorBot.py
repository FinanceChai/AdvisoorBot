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

async def fetch_last_transaction(session, address, last_signature):
    """Fetches the most recent transaction for the given address and checks if it's new compared to the last_signature."""
    params = {'account': address, 'limit': 1, 'offset': 0}
    headers = {'accept': '*/*', 'token': SOLSCAN_API_KEY}
    url = 'https://pro-api.solscan.io/v1.0/account/splTransfers'
    async with session.get(url, params=params, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('data'):
                current_signature = data['data'][0]['signature']
                if current_signature != last_signature:
                    return current_signature, data['data'][0]['tokenAddress']
    return None, None

async def main():
    async with aiohttp.ClientSession() as session:
        # Initialize the last known signatures for each target address
        last_signature = {address: None for address in TARGET_ADDRESSES}
        
        # Populate the initial last known signatures to prevent the first transaction from repeating
        for address in TARGET_ADDRESSES:
            _, initial_signature = await fetch_last_transaction(session, address, None)
            if initial_signature:
                last_signature[address] = initial_signature
        
        # Continuously check for new transactions
        while True:
            await asyncio.sleep(60)  # Check every minute
            for address in TARGET_ADDRESSES:
                new_signature, token_address = await fetch_last_transaction(session, address, last_signature[address])
                if new_signature:
                    print(f"New transaction detected for {address}. Token address: {token_address}")
                    # Update the last known signature to the new one
                    last_signature[address] = new_signature

if __name__ == "__main__":
    asyncio.run(main())

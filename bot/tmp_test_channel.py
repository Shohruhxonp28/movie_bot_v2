import asyncio
import sys
import os

# Add parent dir to sys.path to find 'bot' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from bot.config import settings

async def main():
    print(f"Testing with Token: {settings.BOT_TOKEN[:10]}...")
    print(f"Testing with Channel ID: {settings.PUBLIC_CHANNEL_ID}")
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        chat = await bot.get_chat(settings.PUBLIC_CHANNEL_ID)
        print(f"Chat found: {chat.title} ({chat.type})")
        msg = await bot.send_message(settings.PUBLIC_CHANNEL_ID, "Test message from KinoBot config test.")
        print(f"Message sent! ID: {msg.message_id}")
    except Exception as e:
        print(f"Error type: {type(e)}")
        print(f"Error message: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

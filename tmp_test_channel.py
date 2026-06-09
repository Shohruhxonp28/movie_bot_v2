import asyncio
from aiogram import Bot
from bot.config import settings

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        chat = await bot.get_chat(settings.PUBLIC_CHANNEL_ID)
        print(f"Chat found: {chat.title} ({chat.type})")
        msg = await bot.send_message(settings.PUBLIC_CHANNEL_ID, "Test message from KinoBot config test.")
        print(f"Message sent! ID: {msg.message_id}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

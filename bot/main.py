import asyncio
import logging
from aiogram import Dispatcher, Bot
from bot.loader import bot, dp
from bot.database.session import create_tables
from bot.middlewares import DatabaseMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware

# User handlers
from bot.handlers.user.start import router as start_router
from bot.handlers.user.search import router as search_router
from bot.handlers.user.vip import router as vip_router
from bot.handlers.user.callbacks import router as callbacks_router

# Admin handlers
from bot.handlers.admin.admin import router as admin_router
from bot.handlers.admin.movies import router as movies_router
from bot.handlers.admin.channels import router as channels_router
from bot.handlers.admin.vip import router as vip_admin_router
from bot.handlers.admin.ads import router as ads_router
from bot.handlers.admin.broadcast import router as broadcast_router

# Inline handler
from bot.handlers.inline.inline import router as inline_router


async def on_startup():
    logging.info("Starting KinoBot...")
    
    # Create DB tables and enable extensions
    from bot.database.session import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
        # Alter tables to add new columns if they do not exist
        try:
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS file_id VARCHAR(256);"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS database_message_id BIGINT;"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS serial_link VARCHAR(512);"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS is_vip BOOLEAN DEFAULT FALSE;"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS title VARCHAR(256);"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS description TEXT;"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS short_caption TEXT;"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS views_count INTEGER DEFAULT 0;"))
            await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS downloads_count INTEGER DEFAULT 0;"))
            await conn.execute(text("ALTER TABLE vip_plans ADD COLUMN IF NOT EXISTS name VARCHAR(128);"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_movie_code VARCHAR(32);"))
        except Exception as e:
            logging.warning(f"Note: Table alter update error: {e}")

        # Migrate name_uz to name in vip_plans if name is null
        try:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='vip_plans' AND column_name='name_uz';"
            ))
            if result.fetchone():
                await conn.execute(text("UPDATE vip_plans SET name = name_uz WHERE name IS NULL;"))
        except Exception as e:
            logging.warning(f"Note: Migration of vip_plans.name error: {e}")

        # Migrate movies translation fields to single fields if they are null
        try:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='movies' AND column_name='title_uz';"
            ))
            if result.fetchone():
                await conn.execute(text("UPDATE movies SET title = title_uz WHERE title IS NULL;"))
                await conn.execute(text("UPDATE movies SET description = description_uz WHERE description IS NULL;"))
                await conn.execute(text("UPDATE movies SET short_caption = short_caption_uz WHERE short_caption IS NULL;"))
        except Exception as e:
            logging.warning(f"Note: Migration of movies fields error: {e}")
            
    await create_tables()
    logging.info("Database tables updated and extensions enabled.")

    # Set bot commands
    from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
    
    # Delete old commands first
    await bot.delete_my_commands()
    
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="admin", description="Admin panel"),
    ]
    
    # Set commands for private chats
    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    # Set default commands as well
    await bot.set_my_commands(commands)
    
    logging.info("Bot commands updated successfully!")
    logging.info("Bot started successfully!")


async def on_shutdown():
    logging.info("Shutting down...")
    await bot.session.close()


def register_middlewares():
    # Message middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.inline_query.middleware(DatabaseMiddleware())

    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))

    # Subscription check
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())


def register_routers():
    # Order matters — admin routers first (they have IsAdmin filter)
    dp.include_router(admin_router)
    dp.include_router(movies_router)
    dp.include_router(channels_router)
    dp.include_router(vip_admin_router)
    dp.include_router(ads_router)
    dp.include_router(broadcast_router)

    # User routers
    dp.include_router(start_router)
    dp.include_router(search_router)
    dp.include_router(vip_router)
    dp.include_router(callbacks_router)

    # Inline
    dp.include_router(inline_router)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    register_middlewares()
    register_routers()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

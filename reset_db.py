import asyncio
import logging
from sqlalchemy import text
from bot.database.session import drop_tables, create_tables, engine

logging.basicConfig(level=logging.INFO)


async def main():
    logging.info("Resetting PostgreSQL database...")
    
    # Enable pg_trgm extension first
    async with engine.begin() as conn:
        logging.info("Enabling pg_trgm extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
    logging.info("Dropping all existing tables...")
    await drop_tables()
    
    logging.info("Creating all tables from new schema...")
    await create_tables()
    
    logging.info("Database reset completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from sqlalchemy import select
from bot.database.session import async_session_maker
from bot.database.models import Movie

async def check():
    async with async_session_maker() as s:
        res = await s.execute(select(Movie))
        movies = res.scalars().all()
        print(f'Total: {len(movies)}')
        
        res = await s.execute(select(Movie).where(Movie.is_active == True))
        active_movies = res.scalars().all()
        print(f'Active: {len(active_movies)}')
        
        if active_movies:
            print("Example active movie:", active_movies[0].title_original)

if __name__ == "__main__":
    asyncio.run(check())

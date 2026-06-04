from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from bot.database.models import User, Movie, DownloadLog, SearchLog


class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self) -> dict:
        total_users = (await self.session.execute(
            select(func.count()).select_from(User)
        )).scalar_one()

        vip_users = (await self.session.execute(
            select(func.count()).select_from(User).where(User.is_vip == True)
        )).scalar_one()

        total_movies = (await self.session.execute(
            select(func.count()).select_from(Movie).where(Movie.is_active == True)
        )).scalar_one()

        total_downloads = (await self.session.execute(
            select(func.count()).select_from(DownloadLog)
        )).scalar_one()

        total_searches = (await self.session.execute(
            select(func.count()).select_from(SearchLog)
        )).scalar_one()

        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "total_movies": total_movies,
            "total_downloads": total_downloads,
            "total_searches": total_searches,
        }

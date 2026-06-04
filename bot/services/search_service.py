from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import SearchLog


class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_search(self, user_id: int, query: str, result_count: int):
        log = SearchLog(user_id=user_id, query=query, result_count=result_count)
        self.session.add(log)
        await self.session.commit()

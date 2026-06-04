from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from bot.database.models import Ad


class AdService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_random_ad(self) -> Optional[Ad]:
        result = await self.session.execute(
            select(Ad).where(Ad.is_active == True).order_by(func.random()).limit(1)
        )
        ad = result.scalar_one_or_none()
        if ad:
            ad.impressions += 1
            await self.session.commit()
        return ad

    async def create_ad(self, data: dict) -> Ad:
        ad = Ad(**data)
        self.session.add(ad)
        await self.session.commit()
        await self.session.refresh(ad)
        return ad

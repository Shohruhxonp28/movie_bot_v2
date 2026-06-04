from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import User, VIPPlan, VIPSubscription


class VIPService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_plans(self) -> List[VIPPlan]:
        result = await self.session.execute(
            select(VIPPlan).where(VIPPlan.is_active == True).order_by(VIPPlan.price)
        )
        return result.scalars().all()

    async def get_plan(self, plan_id: int) -> Optional[VIPPlan]:
        result = await self.session.execute(
            select(VIPPlan).where(VIPPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def grant_vip(
        self,
        user_id: int,
        days: int,
        plan_id: Optional[int] = None,
        granted_by: Optional[int] = None,
    ):
        """Grant VIP to a user."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        now = datetime.now()
        # Extend existing VIP if still active
        current_expiry = user.vip_until if user.vip_until and user.vip_until > now else now
        new_expiry = current_expiry + timedelta(days=days)

        user.is_vip = True
        user.vip_until = new_expiry

        sub = VIPSubscription(
            user_id=user_id,
            plan_id=plan_id,
            status="active",
            started_at=now,
            expires_at=new_expiry,
            granted_by=granted_by,
        )
        self.session.add(sub)
        await self.session.commit()

    async def revoke_vip(self, user_id: int):
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_vip = False
            user.vip_until = None
            await self.session.commit()

    async def create_plan(
        self,
        name_uz: str,
        name_ru: str,
        name_en: str,
        duration_days: int,
        price: float,
    ) -> VIPPlan:
        plan = VIPPlan(
            name_uz=name_uz,
            name_ru=name_ru,
            name_en=name_en,
            duration_days=duration_days,
            price=price,
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

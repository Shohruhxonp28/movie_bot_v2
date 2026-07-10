from typing import Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from bot.database.models import User
from bot.config import settings


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self,
        user_id: int,
        username: Optional[str] = None,
        full_name: str = "",
        lang: str = "uz",
    ) -> tuple[User, bool]:
        """Returns (user, is_new)."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            # Update dynamic fields
            user.username = username
            user.full_name = full_name
            await self.session.commit()
            return user, False

        user = User(
            id=user_id,
            username=username,
            full_name=full_name,
            language=lang,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user, True

    async def get(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def set_language(self, user_id: int, lang: str):
        user = await self.get(user_id)
        if user:
            user.language = lang
            await self.session.commit()

    async def set_pending_movie(self, user_id: int, code: Optional[str]):
        user = await self.get(user_id)
        if user:
            user.pending_movie_code = code
            await self.session.commit()

    async def get_pending_movie(self, user_id: int) -> Optional[str]:
        user = await self.get(user_id)
        return user.pending_movie_code if user else None

    async def check_download_limit(self, user_id: int) -> bool:
        """Returns True if user can still download today."""
        user = await self.get(user_id)
        if not user:
            return False

        if user.is_vip and (not user.vip_until or user.vip_until > datetime.now()):
            return True  # VIP has no limit

        today = date.today()
        last_date = user.last_download_date.date() if user.last_download_date else None

        if last_date != today:
            # Reset counter
            user.daily_downloads = 0
            user.last_download_date = datetime.now()
            await self.session.commit()

        limit = settings.DAILY_DOWNLOAD_LIMIT
        return user.daily_downloads < limit

    async def increment_downloads(self, user_id: int):
        user = await self.get(user_id)
        if user:
            today = date.today()
            last_date = user.last_download_date.date() if user.last_download_date else None
            if last_date != today:
                user.daily_downloads = 0
            user.daily_downloads += 1
            user.last_download_date = datetime.now()
            await self.session.commit()

    async def get_downloads_today(self, user_id: int) -> int:
        user = await self.get(user_id)
        if not user:
            return 0
        today = date.today()
        last_date = user.last_download_date.date() if user.last_download_date else None
        if last_date != today:
            return 0
        return user.daily_downloads

    async def is_vip(self, user_id: int) -> bool:
        user = await self.get(user_id)
        if not user:
            return False
        if not user.is_vip:
            return False
        if user.vip_until and user.vip_until < datetime.now():
            user.is_vip = False
            await self.session.commit()
            return False
        return True

    async def ban_user(self, user_id: int):
        user = await self.get(user_id)
        if user:
            user.is_banned = True
            await self.session.commit()

    async def unban_user(self, user_id: int):
        user = await self.get(user_id)
        if user:
            user.is_banned = False
            await self.session.commit()

    async def count_users(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar_one()

    async def count_vip_users(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.is_vip == True)
        )
        return result.scalar_one()

    async def get_all_user_ids(self) -> list[int]:
        result = await self.session.execute(
            select(User.id).where(User.is_banned == False)
        )
        return [row[0] for row in result.fetchall()]

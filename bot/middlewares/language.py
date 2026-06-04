from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import User


class LanguageMiddleware(BaseMiddleware):
    """Inject user language into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        user_id = None

        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        lang = "uz"
        if session and user_id:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                lang = user.language

        data["lang"] = lang
        return await handler(event, data)

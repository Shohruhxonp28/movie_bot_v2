from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Channel, User
from bot.services.subscription_service import SubscriptionService


EXEMPT_CALLBACKS = {"check_subscription", "lang_"}


class SubscriptionMiddleware(BaseMiddleware):
    """Check mandatory channel subscriptions before processing."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Skip for non-user events
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        # Skip subscription check for admins
        from bot.config import settings
        if user.id in settings.admin_ids_list:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        bot: Bot = data.get("bot")

        if not session or not bot:
            return await handler(event, data)

        # Check if subscription check is needed
        svc = SubscriptionService(session, bot)
        not_subscribed = await svc.get_unsubscribed_channels(user.id)

        if not_subscribed:
            lang = data.get("lang", "uz")
            await svc.send_subscription_required(event, not_subscribed, lang)
            return  # block handler

        return await handler(event, data)

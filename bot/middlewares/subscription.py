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

        # Skip subscription check for group chats (e.g. admin group callbacks)
        if isinstance(event, CallbackQuery) and event.message:
            if event.message.chat.type in ("group", "supergroup"):
                return await handler(event, data)

        # Skip subscription check for admins
        from bot.config import settings
        if user.id in settings.admin_ids_list:
            return await handler(event, data)

        # Skip subscription check for /start command
        if isinstance(event, Message) and event.text and event.text.strip().startswith("/start"):
            return await handler(event, data)

        # Skip subscription check if user is uploading VIP payment check
        from aiogram.fsm.context import FSMContext
        state: FSMContext = data.get("state")
        if state:
            current_state = await state.get_state()
            if current_state == "VIPCheckState:waiting_check":
                return await handler(event, data)

        # Skip subscription check for certain callbacks (e.g. check subscription, lang select, VIP flow)
        if isinstance(event, CallbackQuery) and event.data:
            exempt_prefixes = ("lang_", "vip_plan_", "copy_price_", "copy_card_", "vip_send_check_")
            if event.data == "check_subscription" or event.data == "menu_vip" or event.data.startswith(exempt_prefixes):
                return await handler(event, data)

        session: AsyncSession = data.get("session")
        bot: Bot = data.get("bot")

        if not session or not bot:
            return await handler(event, data)

        # Skip subscription check for VIPs
        from bot.services.user_service import UserService
        user_svc = UserService(session)
        if await user_svc.is_vip(user.id):
            return await handler(event, data)

        # Check if subscription check is needed
        svc = SubscriptionService(session, bot)
        not_subscribed = await svc.get_unsubscribed_channels(user.id)

        if not_subscribed:
            lang = data.get("lang", "uz")
            await svc.send_subscription_required(event, not_subscribed, lang)
            return  # block handler

        return await handler(event, data)

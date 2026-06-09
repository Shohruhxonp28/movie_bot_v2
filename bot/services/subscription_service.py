from typing import List, Optional
from aiogram import Bot
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    Message, CallbackQuery
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Channel
from bot.utils.i18n import _
from cachetools import TTLCache
import time

# Cache for subscription status: {user_id: (is_subscribed, timestamp)}
# TTL: 120 seconds (2 minutes)
sub_cache = TTLCache(maxsize=10000, ttl=120)


class SubscriptionService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot

    async def get_required_channels(self) -> List[Channel]:
        result = await self.session.execute(
            select(Channel).where(Channel.is_active == True, Channel.is_required == True)
        )
        return result.scalars().all()

    async def get_unsubscribed_channels(self, user_id: int) -> List[Channel]:
        # Check cache first
        if user_id in sub_cache:
            # If they were fully subscribed, return empty list
            if sub_cache[user_id] is True:
                return []
            # Note: We only cache "True" (fully subscribed) to avoid blocking users
            # if they subscribe and we still have them as "unsubscribed" in cache.
            # But for "lag" issues, catching the "subscribed" state is most important.

        channels = await self.get_required_channels()
        if not channels:
            sub_cache[user_id] = True
            return []

        not_subscribed = []
        for channel in channels:
            try:
                member = await self.bot.get_chat_member(
                    chat_id=int(channel.channel_id),
                    user_id=user_id
                )
                if member.status in ("left", "kicked", "restricted"):
                    not_subscribed.append(channel)
            except Exception:
                # If error (e.g. bot not admin), assume not subscribed or skip?
                # For safety, we assume not subscribed if it's required
                not_subscribed.append(channel)
        
        # Cache the result if they are fully subscribed
        if not not_subscribed:
            sub_cache[user_id] = True
            
        return not_subscribed

    async def is_subscribed(self, user_id: int) -> bool:
        not_subscribed = await self.get_unsubscribed_channels(user_id)
        return len(not_subscribed) == 0

    async def send_subscription_required(
        self,
        event: Message | CallbackQuery,
        channels: List[Channel],
        lang: str = "uz",
    ):
        buttons = []
        for i, ch in enumerate(channels, 1):
            url = ch.invite_link or f"https://t.me/{ch.username.lstrip('@')}" if ch.username else "#"
            buttons.append([InlineKeyboardButton(text=f"📢 {ch.name}", url=url)])
        buttons.append([InlineKeyboardButton(
            text=_("btn_check_sub", lang),
            callback_data="check_subscription"
        )])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        text = _("sub_required", lang)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=kb)
            await event.answer()

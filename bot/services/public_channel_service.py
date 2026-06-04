from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from bot.database.models import Movie
from bot.config import settings
from bot.utils.logger import logger


class PublicChannelService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.channel_id = settings.PUBLIC_CHANNEL_ID
        self.bot_username = settings.BOT_USERNAME

    def _build_keyboard(self, movie: Movie) -> InlineKeyboardMarkup:
        deep_link = f"https://t.me/{self.bot_username}?start=movie_{movie.code}"
        buttons = [[InlineKeyboardButton(text="🎬 Kinoni ko'rish", url=deep_link)]]
        if movie.trailer_type == "url" and movie.trailer_url:
            buttons.insert(0, [InlineKeyboardButton(text="🎬 Treyler/Tizer", url=movie.trailer_url)])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def _build_caption(self, movie: Movie) -> str:
        title = movie.title_uz or movie.title_original
        lines = [f"🎬 Yangi kino!\n"]
        lines.append(f"🎞 Nomi: <b>{title}</b>")
        if movie.year:
            lines.append(f"📅 Yil: {movie.year}")
        if movie.genre:
            lines.append(f"🎭 Janr: {movie.genre}")
        if movie.imdb_rating:
            lines.append(f"⭐ IMDb: {movie.imdb_rating}")

        caption = movie.short_caption_uz or movie.description_uz or ""
        if caption:
            lines.append(f"\n📝 {caption[:200]}")

        lines.append("\n👇 Kinoni botda ko'rish uchun pastdagi tugmani bosing.")
        return "\n".join(lines)

    async def publish_trailer_to_public_channel(self, movie: Movie) -> bool:
        if not self.channel_id:
            return False

        try:
            kb = self._build_keyboard(movie)
            caption = self._build_caption(movie)

            if movie.trailer_type == "video" and movie.trailer_file_id:
                msg = await self.bot.send_video(
                    chat_id=self.channel_id,
                    video=movie.trailer_file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            else:
                msg = await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )

            # Save message id
            movie.public_post_message_id = msg.message_id
            movie.public_posted_at = datetime.now()
            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to post to public channel: {e}")
            return False

    async def update_public_channel_post(self, movie: Movie) -> bool:
        if not self.channel_id or not movie.public_post_message_id:
            return False
        try:
            kb = self._build_keyboard(movie)
            caption = self._build_caption(movie)

            if movie.trailer_type == "video" and movie.trailer_file_id:
                await self.bot.edit_message_caption(
                    chat_id=self.channel_id,
                    message_id=movie.public_post_message_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            else:
                await self.bot.edit_message_text(
                    chat_id=self.channel_id,
                    message_id=movie.public_post_message_id,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            return True
        except Exception as e:
            logger.error(f"Failed to update public channel post: {e}")
            return False

    async def delete_public_channel_post(self, movie: Movie) -> bool:
        if not self.channel_id or not movie.public_post_message_id:
            return False
        try:
            await self.bot.delete_message(
                chat_id=self.channel_id,
                message_id=movie.public_post_message_id,
            )
            movie.public_post_message_id = None
            movie.public_posted_at = None
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete public channel post: {e}")
            return False

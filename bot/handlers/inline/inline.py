from aiogram import Router, F, Bot
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InlineQueryResultPhoto,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.movie_service import MovieService
from bot.utils.i18n import get_movie_caption
from bot.config import settings
import hashlib

router = Router()


@router.inline_query()
async def inline_search(inline_query: InlineQuery, session: AsyncSession):
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=1)
        return

    movie_svc = MovieService(session)
    movies, _ = await movie_svc.smart_search(query, limit=10)

    results = []
    for movie in movies:
        # Use user's language if possible — fallback to uz
        lang = "uz"
        title = getattr(movie, f"title_{lang}", None) or movie.title_original
        year = f" ({movie.year})" if movie.year else ""
        description = getattr(movie, f"short_caption_{lang}", None) or getattr(movie, f"description_{lang}", None) or ""
        description = description[:100] if description else ""

        deep_link = f"https://t.me/{settings.BOT_USERNAME}?start=movie_{movie.code}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎬 Botda ko'rish", url=deep_link)
        ]])

        # Build message content
        lines = [f"🎬 <b>{title}{year}</b>"]
        if movie.genre:
            lines.append(f"🎭 {movie.genre}")
        if movie.imdb_rating:
            lines.append(f"⭐ IMDb: {movie.imdb_rating}")
        if description:
            lines.append(f"\n{description}")
        content_text = "\n".join(lines)

        result_id = hashlib.md5(f"{movie.id}_{query}".encode()).hexdigest()

        if movie.poster_file_id:
            # Use article since we can't directly use file_id in inline photo
            results.append(InlineQueryResultArticle(
                id=result_id,
                title=f"🎬 {title}{year}",
                description=f"{movie.genre or ''} | IMDb: {movie.imdb_rating or '?'} | {description}",
                input_message_content=InputTextMessageContent(
                    message_text=content_text,
                    parse_mode="HTML",
                ),
                reply_markup=kb,
            ))
        else:
            results.append(InlineQueryResultArticle(
                id=result_id,
                title=f"🎬 {title}{year}",
                description=f"{movie.genre or ''} | IMDb: {movie.imdb_rating or '?'} | {description}",
                input_message_content=InputTextMessageContent(
                    message_text=content_text,
                    parse_mode="HTML",
                ),
                reply_markup=kb,
            ))

    await inline_query.answer(results, cache_time=30, is_personal=False)

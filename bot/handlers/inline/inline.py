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

    import html
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

        safe_title = html.escape(title) if title else ""
        safe_description = html.escape(description) if description else ""
        safe_genre = html.escape(movie.genre) if movie.genre else ""

        # Build message content
        lines = [f"🎬 <b>{safe_title}{year}</b>"]
        if movie.genre:
            lines.append(f"🎭 {safe_genre}")
        if movie.imdb_rating:
            lines.append(f"⭐ IMDb: {movie.imdb_rating}")
        if description:
            lines.append(f"\n{safe_description}")
        content_text = "\n".join(lines)

        result_id = hashlib.md5(f"{movie.id}_{query}".encode()).hexdigest()
        
        desc_text = f"{movie.genre or ''} | IMDb: {movie.imdb_rating or '?'} | {description}"
        desc_text = desc_text[:255]

        if movie.poster_file_id:
            try:
                from aiogram.types import InlineQueryResultCachedPhoto
                results.append(InlineQueryResultCachedPhoto(
                    id=result_id,
                    photo_file_id=movie.poster_file_id,
                    title=f"🎬 {title}{year}"[:60],
                    description=desc_text,
                    caption=content_text,
                    parse_mode="HTML",
                    reply_markup=kb,
                ))
            except Exception:
                # Fallback to article if cached photo fails
                results.append(InlineQueryResultArticle(
                    id=result_id,
                    title=f"🎬 {title}{year}"[:60],
                    description=desc_text,
                    input_message_content=InputTextMessageContent(
                        message_text=content_text,
                        parse_mode="HTML",
                    ),
                    reply_markup=kb,
                ))
        else:
            results.append(InlineQueryResultArticle(
                id=result_id,
                title=f"🎬 {title}{year}"[:60],
                description=desc_text,
                input_message_content=InputTextMessageContent(
                    message_text=content_text,
                    parse_mode="HTML",
                ),
                reply_markup=kb,
            ))

    await inline_query.answer(results, cache_time=30, is_personal=False)

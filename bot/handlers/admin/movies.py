import json
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.movie_service import MovieService
from bot.services.ai_service import GeminiService
from bot.services.poster_service import PosterService
from bot.services.public_channel_service import PublicChannelService
from bot.keyboards.admin import (
    admin_main_kb, admin_movie_add_method_kb, admin_movie_confirm_kb,
    admin_movie_actions_kb, admin_movie_type_kb, admin_watermark_kb, admin_back_kb,
)
from bot.utils.helpers import generate_movie_code
from sqlalchemy import select
from bot.database.models import Movie

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Temp storage for AI-generated movie data (keyed by admin user_id)
_temp_movies: dict = {}


class AddMovieState(StatesGroup):
    # AI flow
    ai_waiting_name = State()
    ai_confirm = State()
    # Manual flow
    manual_title = State()
    manual_type = State()
    manual_year = State()
    manual_genre = State()
    manual_imdb = State()
    manual_description = State()
    # Common
    waiting_poster = State()
    waiting_watermark = State()
    waiting_trailer_type = State()
    waiting_trailer = State()


# ─── Movie List ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_movies")
async def adm_movie_list(cb: CallbackQuery, session: AsyncSession):
    movie_svc = MovieService(session)
    movies = await movie_svc.get_all_movies(limit=20)
    total = await movie_svc.count_movies()

    if not movies:
        text = "🎬 Bazada hech qanday kino yo'q."
    else:
        lines = [f"🎬 <b>Kinolar ro'yxati</b> (jami: {total})\n"]
        for m in movies[:15]:
            title = m.title_uz or m.title_original
            lines.append(f"• [{m.code}] {title} ({m.year or '?'})")
        text = "\n".join(lines)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for m in movies[:10]:
        title = m.title_uz or m.title_original
        buttons.append([InlineKeyboardButton(
            text=f"🎬 [{m.code}] {title[:30]}",
            callback_data=f"adm_movie_{m.id}",
        )])
    buttons.append([InlineKeyboardButton(text="➕ Yangi kino", callback_data="adm_add_movie")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()


@router.callback_query(F.data.startswith("adm_movie_") & ~F.data.startswith("adm_movie_edit_") & ~F.data.startswith("adm_movie_delete_"))
async def adm_movie_detail(cb: CallbackQuery, session: AsyncSession):
    movie_id = int(cb.data.split("_")[-1])
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    from bot.config import settings
    deep_link = f"https://t.me/{settings.BOT_USERNAME}?start=movie_{movie.code}"
    text = (
        f"🎬 <b>{movie.title_uz or movie.title_original}</b>\n"
        f"📌 Kod: <code>{movie.code}</code>\n"
        f"📅 Yil: {movie.year or '?'}\n"
        f"🎭 Janr: {movie.genre or '?'}\n"
        f"⭐ IMDb: {movie.imdb_rating or '?'}\n"
        f"👁 Ko'rishlar: {movie.views_count}\n"
        f"🔗 Deep link: <code>{deep_link}</code>"
    )

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=admin_movie_actions_kb(movie_id))
    await cb.answer()


# ─── Add Movie ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_add_movie")
async def adm_add_movie(cb: CallbackQuery):
    await cb.message.edit_text(
        "➕ Kino qo'shish usulini tanlang:",
        reply_markup=admin_movie_add_method_kb(),
    )
    await cb.answer()


# ─── AI Flow ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_add_ai")
async def adm_add_ai_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovieState.ai_waiting_name)
    await cb.message.answer("🤖 Kino nomini yozing (masalan: Interstellar):")
    await cb.answer()


@router.message(AddMovieState.ai_waiting_name)
async def adm_ai_process(message: Message, state: FSMContext, session: AsyncSession):
    movie_name = message.text.strip()
    thinking = await message.answer("🤖 AI ma'lumot tayyarlayapti...")

    gemini = GeminiService()
    data = await gemini.get_movie_info(movie_name)

    await thinking.delete()

    if not data:
        await message.answer("❌ AI ma'lumot tayyorlay olmadi. Qayta urinib ko'ring.")
        await state.clear()
        return

    # Store temp
    temp_id = str(message.from_user.id)
    _temp_movies[temp_id] = data

    await state.set_state(AddMovieState.ai_confirm)

    preview = (
        f"✅ <b>AI tayyorlagan ma'lumot:</b>\n\n"
        f"🎬 Asl nomi: {data.get('title_original', '?')}\n"
        f"🇺🇿 O'zbekcha: {data.get('title_uz', '?')}\n"
        f"🇷🇺 Ruscha: {data.get('title_ru', '?')}\n"
        f"📅 Yil: {data.get('year', '?')}\n"
        f"🎭 Janr: {data.get('genre', '?')}\n"
        f"⭐ IMDb: {data.get('imdb_rating', '?')}\n"
        f"🌍 Davlat: {data.get('country', '?')}\n"
        f"⏱ Davomiyligi: {data.get('duration', '?')} min\n"
        f"🔞 Yosh chegarasi: {data.get('age_limit', '?')}\n\n"
        f"📝 Tavsif:\n{data.get('description_uz', '?')[:200]}..."
    )
    await message.answer(preview, parse_mode="HTML", reply_markup=admin_movie_confirm_kb(temp_id))


@router.callback_query(F.data.startswith("adm_confirm_"))
async def adm_confirm_movie(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    temp_id = cb.data.replace("adm_confirm_", "")
    data = _temp_movies.get(temp_id)

    if not data:
        await cb.answer("Ma'lumot topilmadi", show_alert=True)
        return

    code = generate_movie_code()
    movie_data = {
        "code": code,
        "movie_type": data.get("movie_type", "film"),
        "title_original": data.get("title_original", ""),
        "title_uz": data.get("title_uz"),
        "title_ru": data.get("title_ru"),
        "title_en": data.get("title_en"),
        "description_uz": data.get("description_uz"),
        "description_ru": data.get("description_ru"),
        "description_en": data.get("description_en"),
        "short_caption_uz": data.get("short_caption_uz"),
        "short_caption_ru": data.get("short_caption_ru"),
        "short_caption_en": data.get("short_caption_en"),
        "genre": data.get("genre"),
        "year": data.get("year"),
        "country": data.get("country"),
        "actors": data.get("actors"),
        "imdb_rating": data.get("imdb_rating"),
        "duration": data.get("duration"),
        "age_limit": data.get("age_limit"),
        "keywords": data.get("keywords"),
    }

    movie_svc = MovieService(session)
    movie = await movie_svc.create_movie(movie_data)
    del _temp_movies[temp_id]

    await state.update_data(movie_id=movie.id)
    await state.set_state(AddMovieState.waiting_poster)

    await cb.message.answer(
        f"✅ Kino saqlandi! Kod: <code>{code}</code>\n\n"
        "🖼 Endi poster rasmini yuboring (yoki /skip yozing):",
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "adm_cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await cb.answer()


# ─── Poster Upload ────────────────────────────────────────────────────────────

@router.message(AddMovieState.waiting_poster, F.photo)
async def adm_poster_received(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    movie_id = data.get("movie_id")

    photo: PhotoSize = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    raw = file_bytes.read()

    await state.update_data(raw_poster=raw, poster_file_id=photo.file_id)
    await state.set_state(AddMovieState.waiting_watermark)
    await message.answer(
        "💧 Posterga bot username qo'shilsinmi?",
        reply_markup=admin_watermark_kb(),
    )


@router.message(AddMovieState.waiting_poster, F.text == "/skip")
async def adm_poster_skip(message: Message, state: FSMContext):
    await state.set_state(AddMovieState.waiting_trailer_type)
    await message.answer(
        "🎬 Treyler/Tizer bormi?\n\n"
        "/video — Telegram video yuboraman\n"
        "/url — YouTube/havola beraman\n"
        "/skip — Yo'q",
    )


@router.callback_query(F.data.in_({"adm_wm_yes", "adm_wm_no"}))
async def adm_watermark_choice(cb: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    movie_id = data.get("movie_id")
    raw_poster = data.get("raw_poster")
    poster_file_id = data.get("poster_file_id")

    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)
    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    update_data = {"poster_file_id": poster_file_id}

    if cb.data == "adm_wm_yes" and raw_poster:
        poster_svc = PosterService()
        watermarked = poster_svc.add_watermark(raw_poster, movie_code=movie.code)
        # Upload watermarked photo
        from aiogram.types import BufferedInputFile
        wm_msg = await bot.send_photo(
            chat_id=cb.from_user.id,
            photo=BufferedInputFile(watermarked, filename="poster_wm.jpg"),
            caption="Watermarked poster (saved)",
        )
        update_data["poster_watermarked_file_id"] = wm_msg.photo[-1].file_id

    await movie_svc.update_movie(movie_id, update_data)

    await state.set_state(AddMovieState.waiting_trailer_type)
    await cb.message.answer(
        "🎬 Treyler/Tizer bormi?\n\n"
        "/video — Telegram video yuboraman\n"
        "/url — YouTube/havola beraman\n"
        "/skip — Yo'q",
    )
    await cb.answer()


# ─── Trailer ─────────────────────────────────────────────────────────────────

@router.message(AddMovieState.waiting_trailer_type)
async def adm_trailer_type(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if text == "/video":
        await state.update_data(trailer_type="video")
        await state.set_state(AddMovieState.waiting_trailer)
        await message.answer("📹 Treyler videosini yuboring:")
    elif text == "/url":
        await state.update_data(trailer_type="url")
        await state.set_state(AddMovieState.waiting_trailer)
        await message.answer("🔗 Treyler havolasini yuboring:")
    elif text == "/skip":
        await _finalize_movie(message, state, session=None)
    else:
        await message.answer("/video, /url yoki /skip yozing.")


@router.message(AddMovieState.waiting_trailer, F.video)
async def adm_trailer_video(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    movie_id = data.get("movie_id")
    file_id = message.video.file_id

    movie_svc = MovieService(session)
    await movie_svc.update_movie(movie_id, {
        "trailer_type": "video",
        "trailer_file_id": file_id,
    })
    await _finalize_movie(message, state, session=session, bot=bot)


@router.message(AddMovieState.waiting_trailer, F.text)
async def adm_trailer_url(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    movie_id = data.get("movie_id")
    url = message.text.strip()

    movie_svc = MovieService(session)
    await movie_svc.update_movie(movie_id, {
        "trailer_type": "url",
        "trailer_url": url,
    })
    await _finalize_movie(message, state, session=session, bot=bot)


async def _finalize_movie(message: Message, state: FSMContext, session=None, bot=None):
    data = await state.get_data()
    movie_id = data.get("movie_id")

    if session and movie_id:
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_id(movie_id)
        if movie and bot:
            pub_svc = PublicChannelService(session, bot)
            posted = await pub_svc.publish_trailer_to_public_channel(movie)
            if not posted:
                await message.answer(
                    "✅ Kino saqlandi, lekin publik kanalga post yuborilmadi.\n"
                    "Bot kanal admini ekanini tekshiring."
                )
            else:
                await message.answer("✅ Kino saqlandi va publik kanalga post yuborildi!")
        else:
            await message.answer("✅ Kino muvaffaqiyatli saqlandi!")
    else:
        await message.answer("✅ Kino saqlandi!")

    await state.clear()
    await message.answer("Admin panel:", reply_markup=admin_main_kb())


# ─── Repost to channel ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_repost_"))
async def adm_repost(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    movie_id = int(cb.data.split("_")[-1])
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    pub_svc = PublicChannelService(session, bot)
    if movie.public_post_message_id:
        success = await pub_svc.update_public_channel_post(movie)
    else:
        success = await pub_svc.publish_trailer_to_public_channel(movie)

    if success:
        await cb.answer("✅ Kanal posti yangilandi!", show_alert=True)
    else:
        await cb.answer("❌ Post yuborilmadi. Kanal sozlamalarini tekshiring.", show_alert=True)


# ─── Delete movie ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_movie_delete_"))
async def adm_delete_movie(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    movie_id = int(cb.data.split("_")[-1])
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    # Delete from public channel
    pub_svc = PublicChannelService(session, bot)
    await pub_svc.delete_public_channel_post(movie)
    await movie_svc.delete_movie(movie_id)

    await cb.answer("🗑 Kino o'chirildi", show_alert=True)
    await cb.message.edit_text("🗑 Kino o'chirildi.", reply_markup=admin_main_kb())

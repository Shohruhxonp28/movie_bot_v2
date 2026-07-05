import json
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.movie_service import MovieService
from bot.services.poster_service import PosterService
from bot.keyboards.admin import (
    admin_main_kb, admin_movie_confirm_kb,
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
async def adm_add_movie(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovieState.manual_title)
    await cb.message.edit_text(
        "📝 Kino nomini (original) kiriting:",
        reply_markup=admin_back_kb(),
    )
    await cb.answer()


@router.message(AddMovieState.manual_title)
async def adm_manual_title(message: Message, state: FSMContext):
    await state.update_data(title_original=message.text.strip())
    await state.set_state(AddMovieState.manual_type)
    await message.answer(
        "🎬 Kino turini tanlang:",
        reply_markup=admin_movie_type_kb(),
    )


@router.callback_query(AddMovieState.manual_type, F.data.startswith("adm_type_"))
async def adm_manual_type(cb: CallbackQuery, state: FSMContext):
    m_type = cb.data.replace("adm_type_", "")
    await state.update_data(movie_type=m_type)
    await state.set_state(AddMovieState.manual_year)
    await cb.message.edit_text("📅 Chiqarilgan yili (masalan: 2023):")
    await cb.answer()


@router.message(AddMovieState.manual_year)
async def adm_manual_year(message: Message, state: FSMContext):
    year_text = message.text.strip()
    if not year_text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    await state.update_data(year=int(year_text))
    await state.set_state(AddMovieState.manual_genre)
    await message.answer("🎭 Janrlarini yozing (masalan: Drama, Triller):")


@router.message(AddMovieState.manual_genre)
async def adm_manual_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text.strip())
    await state.set_state(AddMovieState.manual_imdb)
    await message.answer("⭐ IMDb reytingini kiriting (masalan: 8.5):")


@router.message(AddMovieState.manual_imdb)
async def adm_manual_imdb(message: Message, state: FSMContext):
    imdb_text = message.text.strip().replace(",", ".")
    try:
        imdb = float(imdb_text)
    except ValueError:
        await message.answer("❌ To'g'ri son kiriting!")
        return
    await state.update_data(imdb_rating=imdb)
    await state.set_state(AddMovieState.manual_description)
    await message.answer("📝 Kino haqida qisqacha tavsif (o'zbek tilida) yozing:")


@router.message(AddMovieState.manual_description)
async def adm_manual_description(message: Message, state: FSMContext, session: AsyncSession):
    description = message.text.strip()
    data = await state.get_data()
    
    movie_svc = MovieService(session)
    code = await movie_svc.get_next_movie_code()
    movie_data = {
        "code": code,
        "movie_type": data.get("movie_type", "film"),
        "title_original": data.get("title_original"),
        "title_uz": data.get("title_original"), # Temporary default
        "description_uz": description,
        "year": data.get("year"),
        "genre": data.get("genre"),
        "imdb_rating": data.get("imdb_rating"),
    }

    movie = await movie_svc.create_movie(movie_data)
    
    await state.update_data(movie_id=movie.id)
    await state.set_state(AddMovieState.waiting_poster)
    
    await message.answer(
        f"✅ Kino bazaga qo'shildi! Kod: <code>{code}</code>\n\n"
        "🖼 Endi poster rasmini yuboring (yoki /skip):",
        parse_mode="HTML",
    )





@router.callback_query(F.data == "adm_cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await cb.answer()


# ─── Poster Upload ────────────────────────────────────────────────────────────

@router.message(AddMovieState.waiting_poster, F.photo)
async def adm_poster_received(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    photo: PhotoSize = message.photo[-1]
    
    await state.update_data(poster_file_id=photo.file_id)
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
    poster_file_id = data.get("poster_file_id")

    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)
    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    update_data = {"poster_file_id": poster_file_id}

    if cb.data == "adm_wm_yes" and poster_file_id:
        file = await bot.get_file(poster_file_id)
        file_bytes = await bot.download_file(file.file_path)
        raw_poster = file_bytes.read()
        
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
async def adm_trailer_type(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
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
        await _finalize_movie(message, state, session=session, bot=bot)
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


async def _finalize_movie(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    movie_id = data.get("movie_id")
    
    if not movie_id:
        await message.answer("❌ Xatolik: movie_id topilmadi.")
        await state.clear()
        return

    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)
    
    # 2. Transition to adding video file or episodes
    from bot.handlers.admin.versions import AddVersionState, AddEpisodeState
    
    if movie.movie_type in ("film", "multfilm"):
        await state.set_state(AddVersionState.waiting_video)
        await state.update_data(movie_id=movie_id)
        await message.answer(
            "🎬 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            "📹 Endi asosiy videoni (film faylini) yuboring:",
            parse_mode="HTML"
        )
    else:
        # Serial / Anime
        await state.set_state(AddEpisodeState.waiting_episode_number)
        await state.update_data(movie_id=movie_id)
        await message.answer(
            "📺 <b>Serial/Anime saqlandi!</b>\n\n"
            "🔢 Endi birinchi qism raqamini kiriting:",
            parse_mode="HTML"
        )


# ─── Delete movie ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_movie_delete_"))
async def adm_delete_movie(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    movie_id = int(cb.data.split("_")[-1])
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    await movie_svc.delete_movie(movie_id)

    await cb.answer("🗑 Kino o'chirildi", show_alert=True)
    await cb.message.edit_text("🗑 Kino o'chirildi.", reply_markup=admin_main_kb())

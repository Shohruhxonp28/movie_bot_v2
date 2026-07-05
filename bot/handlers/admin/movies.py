from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.movie_service import MovieService
from bot.keyboards.admin import (
    admin_main_kb,
    admin_movie_actions_kb, admin_back_kb,
)
from sqlalchemy import select
from bot.database.models import Movie

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddMovieState(StatesGroup):
    manual_title = State()


class AddSerialState(StatesGroup):
    title = State()
    channel_link = State()


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


@router.callback_query(F.data == "adm_add_serial")
async def adm_add_serial_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddSerialState.title)
    await cb.message.edit_text(
        "📝 Serial nomini kiriting:",
        reply_markup=admin_back_kb(),
    )
    await cb.answer()


@router.message(AddSerialState.title)
async def adm_serial_title(message: Message, state: FSMContext):
    await state.update_data(title_original=message.text.strip())
    await state.set_state(AddSerialState.channel_link)
    await message.answer("🔗 Serial qismlari joylashgan kanal havolasini (linkini) kiriting (masalan: https://t.me/...):")


@router.message(AddSerialState.channel_link)
async def adm_serial_link(message: Message, state: FSMContext, session: AsyncSession):
    link = message.text.strip()
    data = await state.get_data()
    
    movie_svc = MovieService(session)
    code = await movie_svc.get_next_movie_code()
    movie_data = {
        "code": code,
        "movie_type": "serial",
        "title_original": data.get("title_original"),
        "title_uz": data.get("title_original"),
        "serial_link": link,
    }
    
    await movie_svc.create_movie(movie_data)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Serial muvaffaqiyatli saqlandi!</b>\n"
        f"📌 Kod: <code>{code}</code>\n"
        f"🔗 Kanal havolasi: {link}",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )


@router.message(AddMovieState.manual_title)
async def adm_manual_title(message: Message, state: FSMContext, session: AsyncSession):
    title = message.text.strip()
    
    movie_svc = MovieService(session)
    code = await movie_svc.get_next_movie_code()
    movie_data = {
        "code": code,
        "movie_type": "film",
        "title_original": title,
        "title_uz": title,
    }

    movie = await movie_svc.create_movie(movie_data)
    
    # Transition to AddVersionState.waiting_video (from versions.py)
    from bot.handlers.admin.versions import AddVersionState
    await state.set_state(AddVersionState.waiting_video)
    await state.update_data(movie_id=movie.id)
    
    await message.answer(
        f"✅ <b>Kino saqlandi! Kod: <code>{code}</code></b>\n\n"
        f"📹 Endi asosiy videoni (film faylini) yuboring:",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await cb.answer()


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

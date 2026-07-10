from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.movie_service import MovieService
from bot.keyboards.admin import (
    admin_main_kb,
    admin_movie_actions_kb, admin_back_kb, admin_yes_no_kb
)
from sqlalchemy import select
from bot.database.models import Movie
from bot.config import settings

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddMovieState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_poster = State()
    waiting_video = State()
    waiting_is_vip = State()


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
            title = m.title or m.title_original
            lines.append(f"• [{m.code}] {title} ({m.year or '?'})")
        text = "\n".join(lines)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for m in movies[:10]:
        title = m.title or m.title_original
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

    deep_link = f"https://t.me/{settings.BOT_USERNAME}?start=movie_{movie.code}"
    vip_lbl = "Ha 💎" if movie.is_vip else "Yo'q 🆓"
    text = (
        f"🎬 <b>{movie.title or movie.title_original}</b>\n"
        f"📌 Kod: <code>{movie.code}</code>\n"
        f"📅 Yil: {movie.year or '?'}\n"
        f"🎭 Janr: {movie.genre or '?'}\n"
        f"⭐ IMDb: {movie.imdb_rating or '?'}\n"
        f"💎 VIP status: {vip_lbl}\n"
        f"👁 Ko'rishlar: {movie.views_count}\n"
        f"📥 Yuklashlar: {movie.downloads_count}\n"
        f"🔗 Deep link: <code>{deep_link}</code>"
    )

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=admin_movie_actions_kb(movie_id))
    await cb.answer()


# ─── Add Movie (Wizard) ───────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_add_movie")
async def adm_add_movie_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovieState.waiting_title)
    await cb.message.edit_text(
        "📝 Kino nomini kiriting:",
        reply_markup=admin_back_kb(),
    )
    await cb.answer()


@router.message(AddMovieState.waiting_title)
async def adm_add_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieState.waiting_description)
    await message.answer("📝 Kino tavsifini (description) kiriting yoki /skip:")


@router.message(AddMovieState.waiting_description)
async def adm_add_movie_description(message: Message, state: FSMContext):
    desc = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddMovieState.waiting_poster)
    await message.answer("🖼 Rasm formatida poster yuboring yoki /skip:")


@router.message(AddMovieState.waiting_poster)
async def adm_add_movie_poster(message: Message, state: FSMContext):
    if message.text == "/skip":
        await state.update_data(poster_file_id=None)
    elif message.photo:
        await state.update_data(poster_file_id=message.photo[-1].file_id)
    else:
        await message.answer("❌ Iltimos, poster rasmini yuboring yoki /skip deb yozing.")
        return

    await state.set_state(AddMovieState.waiting_video)
    await message.answer("📹 Video fayl yuboring:")


@router.message(AddMovieState.waiting_video, F.video)
async def adm_add_movie_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovieState.waiting_is_vip)
    await message.answer("💎 Ushbu kino faqat VIP a'zolar uchunmi?", reply_markup=admin_yes_no_kb())


@router.callback_query(AddMovieState.waiting_is_vip, F.data.in_({"adm_yes", "adm_no"}))
async def adm_add_movie_is_vip(cb: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    is_vip = cb.data == "adm_yes"
    data = await state.get_data()
    await state.clear()

    movie_svc = MovieService(session)
    code = await movie_svc.get_next_movie_code()

    movie_data = {
        "code": code,
        "movie_type": "film",
        "title_original": data["title"],
        "title": data["title"],
        "description": data["description"],
        "poster_file_id": data["poster_file_id"],
        "file_id": data["file_id"],
        "is_vip": is_vip,
    }

    # If database channel is set, upload video there to keep message_id copy
    database_message_id = None
    if settings.DATABASE_CHANNEL_ID:
        try:
            db_msg = await bot.send_video(
                chat_id=settings.DATABASE_CHANNEL_ID,
                video=data["file_id"],
                caption=f"🎬 {data['title']}\n📌 Kod: {code}\n💎 VIP: {'Ha' if is_vip else 'Yoq'}"
            )
            database_message_id = db_msg.message_id
        except Exception as e:
            await cb.message.answer(f"⚠️ Bazaga (kanalga) saqlashda xatolik: {e}")

    movie_data["database_message_id"] = database_message_id

    movie = await movie_svc.create_movie(movie_data)

    await cb.message.edit_text(
        f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
        f"🎬 Nomi: <b>{movie.title}</b>\n"
        f"📌 Kod: <code>{code}</code>\n"
        f"💎 VIP: <b>{'Ha' if is_vip else 'Yoq'}</b>",
        parse_mode="HTML",
        reply_markup=admin_main_kb(),
    )
    await cb.answer()


# ─── Add Serial ───────────────────────────────────────────────────────────────

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
    await state.update_data(title=message.text.strip())
    await state.set_state(AddSerialState.channel_link)
    await message.answer("🔗 Serial qismlari joylashgan kanal havolasini (linkini) kiriting:")


@router.message(AddSerialState.channel_link)
async def adm_serial_link(message: Message, state: FSMContext, session: AsyncSession):
    link = message.text.strip()
    data = await state.get_data()
    
    movie_svc = MovieService(session)
    code = await movie_svc.get_next_movie_code()
    movie_data = {
        "code": code,
        "movie_type": "serial",
        "title_original": data.get("title"),
        "title": data.get("title"),
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


@router.callback_query(F.data == "adm_cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await cb.answer()


# ─── Delete movie ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_movie_delete_"))
async def adm_delete_movie(cb: CallbackQuery, session: AsyncSession):
    movie_id = int(cb.data.split("_")[-1])
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    await movie_svc.delete_movie(movie_id)

    await cb.answer("🗑 Kino o'chirildi", show_alert=True)
    await cb.message.edit_text("🗑 Kino o'chirildi.", reply_markup=admin_main_kb())

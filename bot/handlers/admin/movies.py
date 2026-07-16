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
    waiting_video = State()


class AddSerialState(StatesGroup):
    title = State()
    channel_link = State()


# ─── Movie List ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_movies"))
async def adm_movie_list(cb: CallbackQuery, session: AsyncSession):
    parts = cb.data.split("_")
    page = 1
    if len(parts) > 2 and parts[2] == "page":
        try:
            page = int(parts[3])
        except (IndexError, ValueError):
            page = 1

    movie_svc = MovieService(session)
    limit = 10
    offset = (page - 1) * limit
    movies = await movie_svc.get_all_movies(limit=limit, offset=offset)
    total = await movie_svc.count_movies()
    import math
    total_pages = math.ceil(total / limit) or 1

    if not movies:
        text = "🎬 Bazada hech qanday kino yo'q."
    else:
        lines = [f"🎬 <b>Kinolar ro'yxati</b> (Jami: {total}, Sahifa: {page}/{total_pages})\n"]
        for m in movies:
            title = m.title or m.title_original
            lines.append(f"• [{m.code}] {title} ({m.year or '?'})")
        text = "\n".join(lines)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for m in movies:
        title = m.title or m.title_original
        buttons.append([InlineKeyboardButton(
            text=f"🎬 [{m.code}] {title[:30]}",
            callback_data=f"adm_movie_{m.id}",
        )])

    # Pagination controls
    pagination_row = []
    if page > 1:
        pagination_row.append(InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"adm_movies_page_{page - 1}"))
    pagination_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        pagination_row.append(InlineKeyboardButton(text="▶️ Keyingi", callback_data=f"adm_movies_page_{page + 1}"))
    buttons.append(pagination_row)

    buttons.append([InlineKeyboardButton(text="➕ Yangi kino", callback_data="adm_add_movie")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()


@router.callback_query(F.data.startswith("adm_movie_") & ~F.data.startswith("adm_movie_edit_") & ~F.data.startswith("adm_movie_delete_") & ~F.data.startswith("adm_movies"))
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
        f"📹 File ID: {'Mavjud' if movie.file_id else 'Yoq'}\n"
        f"🆔 DB Msg ID: {movie.database_message_id or 'Yoq'}\n"
        f"🔗 Serial Link: {movie.serial_link or 'Yoq'}\n"
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
    await state.set_state(AddMovieState.waiting_video)
    await message.answer("📹 Video fayl yuboring:")


@router.message(AddMovieState.waiting_video, F.video)
async def adm_add_movie_video(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    file_id = message.video.file_id
    data = await state.get_data()
    await state.clear()

    movie_svc = MovieService(session)
    code = await movie_svc.get_next_movie_code()

    movie_data = {
        "code": code,
        "movie_type": "film",
        "title_original": data["title"],
        "title": data["title"],
        "description": None,
        "poster_file_id": None,
        "file_id": file_id,
        "is_vip": False,
    }

    # If database channel is set, upload video there to keep message_id copy
    database_message_id = None
    if settings.DATABASE_CHANNEL_ID:
        try:
            db_msg = await bot.send_video(
                chat_id=settings.DATABASE_CHANNEL_ID,
                video=file_id,
                caption=f"🎬 {data['title']}\n📌 Kod: {code}"
            )
            database_message_id = db_msg.message_id
        except Exception as e:
            await message.answer(f"⚠️ Bazaga (kanalga) saqlashda xatolik: {e}")

    movie_data["database_message_id"] = database_message_id

    movie = await movie_svc.create_movie(movie_data)

    await message.answer(
        f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
        f"🎬 Nomi: <b>{movie.title}</b>\n"
        f"📌 Kod: <code>{code}</code>",
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


# ─── Edit movie ───────────────────────────────────────────────────────────────

class EditMovieState(StatesGroup):
    waiting_new_value = State()


async def adm_movie_detail_helper(cb: CallbackQuery, movie_id: int, session: AsyncSession):
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)
    if not movie:
        await cb.message.edit_text("Kino topilmadi.", reply_markup=admin_main_kb())
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
        f"📹 File ID: {'Mavjud' if movie.file_id else 'Yoq'}\n"
        f"🆔 DB Msg ID: {movie.database_message_id or 'Yoq'}\n"
        f"🔗 Serial Link: {movie.serial_link or 'Yoq'}\n"
        f"👁 Ko'rishlar: {movie.views_count}\n"
        f"📥 Yuklashlar: {movie.downloads_count}\n"
        f"🔗 Deep link: <code>{deep_link}</code>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=admin_movie_actions_kb(movie_id))


@router.callback_query(F.data.startswith("adm_movie_edit_"))
async def adm_movie_edit_choices(cb: CallbackQuery, session: AsyncSession):
    movie_id = int(cb.data.split("_")[-1])
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)
    if not movie:
        await cb.answer("Kino topilmadi", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nomi", callback_data=f"adm_med_title_{movie_id}"),
            InlineKeyboardButton(text="📝 Tavsif", callback_data=f"adm_med_desc_{movie_id}"),
        ],
        [
            InlineKeyboardButton(text="📌 Kod", callback_data=f"adm_med_code_{movie_id}"),
            InlineKeyboardButton(text="🖼 Poster", callback_data=f"adm_med_poster_{movie_id}"),
        ],
        [
            InlineKeyboardButton(text="📹 Video", callback_data=f"adm_med_video_{movie_id}"),
            InlineKeyboardButton(text="💎 VIP Toggle", callback_data=f"adm_med_vip_{movie_id}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Bekor qilish", callback_data=f"adm_movie_{movie_id}"),
        ]
    ])

    await cb.message.edit_text(
        f"✏️ <b>Kino tahrirlash</b>: <b>{movie.title}</b>\n\nTahrirlamoqchi bo'lgan maydoningizni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm_med_"))
async def adm_movie_edit_field_selected(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = cb.data.split("_")
    field = parts[2]
    movie_id = int(parts[3])

    if field == "vip":
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_id(movie_id)
        if movie:
            movie.is_vip = not movie.is_vip
            await session.commit()
            await cb.answer(f"💎 VIP status o'zgartirildi: {'Ha' if movie.is_vip else 'Yoq'}", show_alert=True)
            await adm_movie_detail_helper(cb, movie_id, session)
        return

    await state.set_state(EditMovieState.waiting_new_value)
    await state.update_data(movie_id=movie_id, field=field)

    prompts = {
        "title": "📝 Yangi nom kiriting:",
        "desc": "📝 Yangi tavsif kiriting (yoki o'chirish uchun /delete):",
        "code": "📌 Yangi qidiruv kodini kiriting:",
        "poster": "🖼 Yangi rasmli poster yuboring (yoki o'chirish uchun /delete):",
        "video": "📹 Yangi video fayl yuboring:",
    }

    await cb.message.edit_text(prompts.get(field, "Yozing:"), reply_markup=admin_back_kb())
    await cb.answer()


@router.message(EditMovieState.waiting_new_value)
async def adm_movie_edit_save(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    await state.clear()

    movie_id = data["movie_id"]
    field = data["field"]

    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(movie_id)
    if not movie:
        await message.answer("Kino topilmadi.")
        return

    if field == "title":
        movie.title = message.text.strip()
        movie.title_original = message.text.strip()
    elif field == "desc":
        movie.description = None if message.text.strip() == "/delete" else message.text.strip()
    elif field == "code":
        code = message.text.strip()
        existing = await movie_svc.get_by_code(code)
        if existing and existing.id != movie_id:
            await message.answer("❌ Bu kod boshqa kino uchun ishlatilgan! Yangi qiymat yuboring:")
            await state.set_state(EditMovieState.waiting_new_value)
            await state.update_data(movie_id=movie_id, field=field)
            return
        movie.code = code
    elif field == "poster":
        if message.text == "/delete":
            movie.poster_file_id = None
        elif message.photo:
            movie.poster_file_id = message.photo[-1].file_id
        else:
            await message.answer("❌ Iltimos, poster rasmini yuboring (yoki o'chirish uchun /delete):")
            await state.set_state(EditMovieState.waiting_new_value)
            await state.update_data(movie_id=movie_id, field=field)
            return
    elif field == "video":
        if message.video:
            movie.file_id = message.video.file_id
            if settings.DATABASE_CHANNEL_ID:
                try:
                    db_msg = await bot.send_video(
                        chat_id=settings.DATABASE_CHANNEL_ID,
                        video=message.video.file_id,
                        caption=f"🎬 {movie.title}\n📌 Kod: {movie.code}\n💎 VIP: {'Ha' if movie.is_vip else 'Yoq'}"
                    )
                    movie.database_message_id = db_msg.message_id
                except Exception as e:
                    await message.answer(f"⚠️ Bazaga yuborishda xatolik: {e}")
        else:
            await message.answer("❌ Iltimos, video fayl yuboring:")
            await state.set_state(EditMovieState.waiting_new_value)
            await state.update_data(movie_id=movie_id, field=field)
            return

    await session.commit()
    await message.answer(f"✅ Tahrirlandi!", reply_markup=admin_main_kb())

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
    await message.answer(text, parse_mode="HTML", reply_markup=admin_movie_actions_kb(movie_id))

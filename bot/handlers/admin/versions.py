from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.movie_service import MovieService
from bot.keyboards.admin import (
    admin_quality_kb, admin_language_kb, admin_dub_type_kb,
    admin_premium_kb, admin_back_kb, admin_main_kb,
)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddVersionState(StatesGroup):
    waiting_movie_id = State()
    waiting_video = State()
    waiting_quality = State()
    waiting_language = State()
    waiting_dub_type = State()
    waiting_premium = State()
    waiting_size = State()


class AddEpisodeState(StatesGroup):
    waiting_episode_number = State()
    waiting_episode_title = State()
    waiting_video = State()
    waiting_quality = State()
    waiting_language = State()
    waiting_dub_type = State()
    waiting_premium = State()


# ─── Add Version ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_addver_"))
async def adm_add_version_start(cb: CallbackQuery, state: FSMContext):
    movie_id = int(cb.data.split("_")[-1])
    await state.update_data(movie_id=movie_id)
    await state.set_state(AddVersionState.waiting_video)
    await cb.message.answer("📹 Video faylni yuboring:")
    await cb.answer()


@router.message(AddVersionState.waiting_video, F.video)
async def adm_version_video(message: Message, state: FSMContext):
    file_id = message.video.file_id
    await state.update_data(file_id=file_id, quality="Auto")
    await state.set_state(AddVersionState.waiting_language)
    await message.answer("🌐 Tilni tanlang:", reply_markup=admin_language_kb())


@router.callback_query(AddVersionState.waiting_language, F.data.startswith("adm_lang_"))
async def adm_version_language(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.replace("adm_lang_", "")
    await state.update_data(language=lang)
    await state.set_state(AddVersionState.waiting_dub_type)
    await cb.message.answer("🎙 Dublyaj turini tanlang:", reply_markup=admin_dub_type_kb())
    await cb.answer()


@router.callback_query(AddVersionState.waiting_dub_type, F.data.startswith("adm_dub_"))
async def adm_version_dub(cb: CallbackQuery, state: FSMContext):
    dub = cb.data.replace("adm_dub_", "")
    if dub == "skip":
        dub = "professional"
    await state.update_data(dub_type=dub)
    await state.set_state(AddVersionState.waiting_premium)
    await cb.message.answer("💎 Versiya turi:", reply_markup=admin_premium_kb())
    await cb.answer()


@router.callback_query(AddVersionState.waiting_premium, F.data.in_({"adm_prem_yes", "adm_prem_no"}))
async def adm_version_premium(cb: CallbackQuery, state: FSMContext):
    is_premium = cb.data == "adm_prem_yes"
    await state.update_data(is_premium=is_premium)
    await state.set_state(AddVersionState.waiting_size)
    await cb.message.answer("📦 Fayl hajmini yozing (masalan: 1.4 GB) yoki /skip:")
    await cb.answer()


@router.message(AddVersionState.waiting_size)
async def adm_version_size(message: Message, state: FSMContext, session: AsyncSession):
    size = None if message.text.strip() == "/skip" else message.text.strip()
    data = await state.get_data()
    movie_svc = MovieService(session)
    movie = await movie_svc.get_by_id(data["movie_id"])

    from bot.config import settings
    database_message_id = None
    if settings.DATABASE_CHANNEL_ID:
        try:
            db_msg = await message.bot.send_video(
                chat_id=settings.DATABASE_CHANNEL_ID,
                video=data["file_id"],
                caption=f"🎬 {movie.title_uz or movie.title_original}\n📌 Kod: {movie.code}\n✅ {data['quality']} | {data['language']}"
            )
            database_message_id = db_msg.message_id
        except Exception as e:
            await message.answer(f"⚠️ Bazaga (kanalga) saqlashda xatolik: {e}")

    version_data = {
        "movie_id": data["movie_id"],
        "file_id": data["file_id"],
        "quality": data["quality"],
        "language": data["language"],
        "dub_type": data["dub_type"],
        "is_premium": data["is_premium"],
        "file_size": size,
        "database_message_id": database_message_id,
    }

    movie_svc = MovieService(session)
    version = await movie_svc.add_movie_version(version_data)

    from bot.utils.helpers import format_version_button
    await message.answer(
        f"✅ Versiya qo'shildi:\n{format_version_button(version)}",
        reply_markup=admin_main_kb(),
    )
    await state.clear()


# ─── Add Episode ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_addep_"))
async def adm_add_episode_start(cb: CallbackQuery, state: FSMContext):
    movie_id = int(cb.data.split("_")[-1])
    await state.update_data(movie_id=movie_id)
    await state.set_state(AddEpisodeState.waiting_episode_number)
    await cb.message.answer("🔢 Qism raqamini yozing (masalan: 1):")
    await cb.answer()


@router.message(AddEpisodeState.waiting_episode_number)
async def adm_episode_number(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yozing.")
        return
    await state.update_data(episode_number=int(message.text.strip()))
    await state.set_state(AddEpisodeState.waiting_episode_title)
    await message.answer("📝 Qism nomini yozing (masalan: Birinchi qism) yoki /skip:")


@router.message(AddEpisodeState.waiting_episode_title)
async def adm_episode_title(message: Message, state: FSMContext, session: AsyncSession):
    title = None if message.text.strip() == "/skip" else message.text.strip()
    data = await state.get_data()

    movie_svc = MovieService(session)
    episode = await movie_svc.add_episode(
        movie_id=data["movie_id"],
        episode_number=data["episode_number"],
        title=title,
    )
    await state.update_data(episode_id=episode.id)
    await state.set_state(AddEpisodeState.waiting_video)
    await message.answer(
        f"✅ Qism #{data['episode_number']} yaratildi.\n\n"
        "📹 Endi qism videosini yuboring (yoki /skip — keyinroq qo'shaman):"
    )


@router.message(AddEpisodeState.waiting_video, F.text == "/skip")
async def adm_episode_video_skip(message: Message, state: FSMContext):
    await message.answer("✅ Qism saqlandi. Versiyani keyinroq qo'shishingiz mumkin.", reply_markup=admin_main_kb())
    await state.clear()


@router.message(AddEpisodeState.waiting_video, F.video)
async def adm_episode_video(message: Message, state: FSMContext):
    file_id = message.video.file_id
    await state.update_data(ep_file_id=file_id, ep_quality="Auto")
    await state.set_state(AddEpisodeState.waiting_language)
    await message.answer("🌐 Tilni tanlang:", reply_markup=admin_language_kb())


@router.callback_query(AddEpisodeState.waiting_language, F.data.startswith("adm_lang_"))
async def adm_ep_language(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.replace("adm_lang_", "")
    await state.update_data(ep_language=lang)
    await state.set_state(AddEpisodeState.waiting_dub_type)
    await cb.message.answer("🎙 Dublyaj turini tanlang:", reply_markup=admin_dub_type_kb())
    await cb.answer()


@router.callback_query(AddEpisodeState.waiting_dub_type, F.data.startswith("adm_dub_"))
async def adm_ep_dub(cb: CallbackQuery, state: FSMContext):
    dub = cb.data.replace("adm_dub_", "")
    if dub == "skip":
        dub = "professional"
    await state.update_data(ep_dub=dub)
    await state.set_state(AddEpisodeState.waiting_premium)
    await cb.message.answer("💎 Versiya turi:", reply_markup=admin_premium_kb())
    await cb.answer()


@router.callback_query(AddEpisodeState.waiting_premium, F.data.in_({"adm_prem_yes", "adm_prem_no"}))
async def adm_ep_premium(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    is_premium = cb.data == "adm_prem_yes"
    data = await state.get_data()
    movie_svc = MovieService(session)
    from bot.database.models import Episode, Movie
    result = await session.execute(
        select(Movie).join(Episode).where(Episode.id == data["episode_id"])
    )
    movie = result.scalar_one_or_none()
    res_ep = await session.execute(select(Episode).where(Episode.id == data["episode_id"]))
    episode = res_ep.scalar_one_or_none()

    from bot.config import settings
    database_message_id = None
    if settings.DATABASE_CHANNEL_ID and movie and episode:
        try:
            db_msg = await cb.bot.send_video(
                chat_id=settings.DATABASE_CHANNEL_ID,
                video=data["ep_file_id"],
                caption=f"🎬 {movie.title_uz or movie.title_original}\n🔢 Qism: {episode.episode_number}\n📌 Kod: {movie.code}\n✅ {data['ep_quality']} | {data['ep_language']}"
            )
            database_message_id = db_msg.message_id
        except Exception as e:
            await cb.message.answer(f"⚠️ Bazaga (kanalga) saqlashda xatolik: {e}")

    ep_version_data = {
        "episode_id": data["episode_id"],
        "file_id": data["ep_file_id"],
        "quality": data["ep_quality"],
        "language": data["ep_language"],
        "dub_type": data["ep_dub"],
        "is_premium": is_premium,
        "database_message_id": database_message_id,
    }

    movie_svc = MovieService(session)
    await movie_svc.add_episode_version(ep_version_data)

    await cb.message.answer(
        f"✅ Qism versiyasi qo'shildi: {data['ep_quality']} | {data['ep_language']}",
        reply_markup=admin_main_kb(),
    )
    await state.clear()
    await cb.answer()

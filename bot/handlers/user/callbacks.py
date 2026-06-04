from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.movie_service import MovieService
from bot.services.ad_service import AdService
from bot.keyboards.user import (
    movie_versions_kb, episode_versions_kb, vip_required_kb,
    main_menu_kb,
)
from bot.utils.i18n import _

router = Router()


@router.callback_query(F.data.startswith("movie_watch_"))
async def movie_watch(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    movie_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer(_("movie_not_found", lang), show_alert=True)
        return

    versions = await movie_svc.get_active_versions(movie_id)

    if not versions:
        await cb.answer(_("movie_no_versions", lang), show_alert=True)
        return

    if len(versions) == 1:
        # Direct send
        version = versions[0]
        await _send_version(cb, version, user, lang, movie_id, session, bot)
    else:
        # Show version selection
        await cb.message.answer(
            _("choose_version", lang),
            reply_markup=movie_versions_kb(versions, lang),
        )
    await cb.answer()


@router.callback_query(F.data.startswith("ver_"))
async def version_selected(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    version_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    version = await movie_svc.get_version(version_id)

    if not version:
        await cb.answer(_("movie_not_found", lang), show_alert=True)
        return

    await _send_version(cb, version, user, lang, version.movie_id, session, bot)
    await cb.answer()


@router.callback_query(F.data.startswith("ep_"))
async def episode_selected(cb: CallbackQuery, session: AsyncSession):
    episode_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    versions = await movie_svc.get_episode_active_versions(episode_id)

    if not versions:
        await cb.answer(_("movie_no_versions", lang), show_alert=True)
        return

    if len(versions) == 1:
        version = versions[0]
        await _send_episode_version(cb, version, user, lang, session)
    else:
        await cb.message.answer(
            _("choose_version", lang),
            reply_markup=episode_versions_kb(versions, lang),
        )
    await cb.answer()


@router.callback_query(F.data.startswith("epver_"))
async def episode_version_selected(cb: CallbackQuery, session: AsyncSession):
    version_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    version = await movie_svc.get_episode_version(version_id)
    if not version:
        await cb.answer(_("movie_not_found", lang), show_alert=True)
        return

    await _send_episode_version(cb, version, user, lang, session)
    await cb.answer()


@router.callback_query(F.data.startswith("movie_trailer_"))
async def movie_trailer(cb: CallbackQuery, session: AsyncSession):
    movie_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer(_("movie_not_found", lang), show_alert=True)
        return

    if movie.trailer_type == "video" and movie.trailer_file_id:
        await cb.message.answer_video(video=movie.trailer_file_id)
    elif movie.trailer_type == "url" and movie.trailer_url:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎬 Treyler ko'rish", url=movie.trailer_url)
        ]])
        trailer_text = {"uz": "🎬 Treyler:", "ru": "🎬 Трейлер:", "en": "🎬 Trailer:"}
        await cb.message.answer(trailer_text.get(lang, "🎬"), reply_markup=kb)
    else:
        await cb.answer("Treyler topilmadi", show_alert=True)
        return

    await cb.answer()


@router.callback_query(F.data.startswith("movie_save_"))
async def movie_save(cb: CallbackQuery, session: AsyncSession):
    movie_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    saved = await movie_svc.toggle_save(cb.from_user.id, movie_id)
    msg = _("movie_saved", lang) if saved else _("movie_unsaved", lang)
    await cb.answer(msg, show_alert=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _send_version(cb, version, user, lang, movie_id, session, bot):
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    # VIP check
    if version.is_premium and not await user_svc.is_vip(user.id):
        await cb.message.answer(
            _("vip_required", lang),
            reply_markup=vip_required_kb(lang),
        )
        return

    # Download limit check
    if not await user_svc.check_download_limit(user.id):
        await cb.message.answer(
            _("download_limit", lang),
            reply_markup=vip_required_kb(lang),
        )
        return

    await cb.message.answer_video(video=version.file_id)
    await user_svc.increment_downloads(user.id)
    await movie_svc.increment_version_downloads(version.id)
    await movie_svc.log_download(user.id, movie_id, version.id)

    # Show ad for non-VIP users
    if not await user_svc.is_vip(user.id):
        ad_svc = AdService(session)
        ad = await ad_svc.get_random_ad()
        if ad and ad.show_after_download:
            await _send_ad(cb.message, ad)


async def _send_episode_version(cb, version, user, lang, session):
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    # VIP check
    if version.is_premium and not await user_svc.is_vip(user.id):
        await cb.message.answer(
            _("vip_required", lang),
            reply_markup=vip_required_kb(lang),
        )
        return

    # Download limit
    if not await user_svc.check_download_limit(user.id):
        await cb.message.answer(
            _("download_limit", lang),
            reply_markup=vip_required_kb(lang),
        )
        return

    await cb.message.answer_video(video=version.file_id)
    await user_svc.increment_downloads(user.id)
    await movie_svc.increment_episode_version_downloads(version.id)


async def _send_ad(message, ad):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = None
    if ad.button_text and ad.button_url:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=ad.button_text, url=ad.button_url)
        ]])

    if ad.media_file_id and ad.media_type == "photo":
        await message.answer_photo(photo=ad.media_file_id, caption=ad.text, reply_markup=kb)
    elif ad.media_file_id and ad.media_type == "video":
        await message.answer_video(video=ad.media_file_id, caption=ad.text, reply_markup=kb)
    else:
        await message.answer(ad.text, reply_markup=kb)

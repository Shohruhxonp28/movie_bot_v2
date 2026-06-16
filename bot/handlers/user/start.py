from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.movie_service import MovieService
from bot.services.subscription_service import SubscriptionService
from bot.keyboards.user import main_menu_kb, language_select_kb
from bot.utils.i18n import _, get_movie_caption
from bot.config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot,
):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name or ""

    user_svc = UserService(session)
    user, is_new = await user_svc.get_or_create(
        user_id=user_id,
        username=username,
        full_name=full_name,
    )
    lang = user.language

    # Parse deep link argument
    args = command.args or ""

    # Handle referral
    if args.startswith("ref_"):
        referrer_id_str = args[4:]
        if referrer_id_str.isdigit():
            referrer_id = int(referrer_id_str)
            if is_new and referrer_id != user_id:
                await user_svc.process_referral(user_id, referrer_id)

    # Handle movie deep link
    elif args.startswith("movie_"):
        movie_code = args[6:]
        # Check subscription first
        sub_svc = SubscriptionService(session, bot)
        not_subscribed = await sub_svc.get_unsubscribed_channels(user_id)

        if not_subscribed:
            # Save pending movie
            await user_svc.set_pending_movie(user_id, movie_code)
            await sub_svc.send_subscription_required(message, not_subscribed, lang)
            return

        # Deliver the movie
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_code(movie_code)
        if not movie:
            await message.answer(_("movie_not_found", lang))
        else:
            await deliver_movie(message, movie, user, lang, session, bot)
        return

    # New user — language selection
    if is_new or not user.language:
        await message.answer(
            _("welcome_new", lang),
            reply_markup=language_select_kb(),
        )
        return

    # Return: pending movie (after subscription)
    if user.pending_movie_code:
        code = user.pending_movie_code
        await user_svc.set_pending_movie(user_id, None)
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_code(code)
        if movie:
            await deliver_movie(message, movie, user, lang, session, bot)
            return

    # Main menu
    await message.answer(
        _("welcome_back", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = cb.from_user.id
    user_svc = UserService(session)
    user = await user_svc.get(user_id)
    lang = user.language if user else "uz"

    sub_svc = SubscriptionService(session, bot)
    not_subscribed = await sub_svc.get_unsubscribed_channels(user_id)

    if not_subscribed:
        await cb.answer(_("sub_not_completed", lang), show_alert=True)
        return

    await cb.answer("✅")

    # Check pending movie
    if user and user.pending_movie_code:
        code = user.pending_movie_code
        await user_svc.set_pending_movie(user_id, None)
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_code(code)
        if movie:
            await deliver_movie(cb.message, movie, user, lang, session, bot)
            return

    await cb.message.answer(
        _("welcome_back", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "go_main_menu")
async def go_main_menu(cb: CallbackQuery, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    await cb.message.answer(
        _("welcome_back", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML",
    )
    await cb.answer()


async def deliver_movie(
    message: Message,
    movie,
    user,
    lang: str,
    session: AsyncSession,
    bot: Bot,
):
    """Send movie info and handle version selection / direct send."""
    from bot.keyboards.user import movie_actions_kb, movie_versions_kb, episode_select_kb
    from bot.services.movie_service import MovieService

    movie_svc = MovieService(session)
    is_saved = await movie_svc.is_saved(user.id, movie.id)
    await movie_svc.increment_views(movie.id)

    caption = get_movie_caption(movie, lang)
    has_trailer = movie.trailer_type != "none" and (movie.trailer_file_id or movie.trailer_url)
    active_versions = await movie_svc.get_active_versions(movie.id)

    kb = movie_actions_kb(
        movie_id=movie.id,
        has_trailer=bool(has_trailer),
        has_versions=bool(active_versions),
        is_saved=is_saved,
        lang=lang,
    )

    from bot.config import settings
    if movie.public_post_message_id and settings.PUBLIC_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=settings.PUBLIC_CHANNEL_ID,
                message_id=movie.public_post_message_id,
                reply_markup=kb,
            )
        except Exception:
            if movie.poster_file_id:
                await message.answer_photo(
                    photo=movie.poster_watermarked_file_id or movie.poster_file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
            else:
                await message.answer(caption, parse_mode="HTML", reply_markup=kb)
    else:
        if movie.poster_file_id:
            await message.answer_photo(
                photo=movie.poster_watermarked_file_id or movie.poster_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=kb)

    # If serial/anime — show episode buttons
    if movie.movie_type in ("serial", "anime") and movie.episodes:
        from bot.keyboards.user import episode_select_kb
        await message.answer(
            _("choose_episode", lang),
            reply_markup=episode_select_kb(movie.episodes, lang),
        )

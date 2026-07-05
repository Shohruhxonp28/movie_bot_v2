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

from aiogram.fsm.context import FSMContext

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
):
    await state.clear()
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

    # Notify admins about new user
    if is_new:
        from bot.utils.logger import logger
        user_mention = f"@{username}" if username else f"ID: {user_id}"
        admin_text = (
            f"👤 <b>Yangi foydalanuvchi!</b>\n\n"
            f"👤 Ism: <b>{full_name}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"🔗 Username: {user_mention}\n"
        )
        if args.startswith("ref_"):
            admin_text += f"👥 Kim orqali: <code>{args[4:]}</code>"

        # Send to group
        if settings.ADMIN_GROUP_ID:
            try:
                await bot.send_message(settings.ADMIN_GROUP_ID, admin_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Error sending new user notify to group: {e}")
        
        # Send to individual admins
        for adm_id in settings.admin_ids_list:
            try:
                await bot.send_message(adm_id, admin_text, parse_mode="HTML")
            except Exception:
                pass

    # 1. VIP/Subscription Check
    sub_svc = SubscriptionService(session, bot)
    is_vip = await user_svc.is_vip(user_id)
    not_subscribed = [] if is_vip else await sub_svc.get_unsubscribed_channels(user_id)

    if not_subscribed:
        # If user has a movie deep link, save it so we deliver it after they subscribe
        if args.startswith("movie_"):
            movie_code = args[6:]
            await user_svc.set_pending_movie(user_id, movie_code)
        
        await sub_svc.send_subscription_required(message, not_subscribed, lang)
        return

    # 2. Handle movie deep link if they are subscribed or VIP
    if args.startswith("movie_"):
        movie_code = args[6:]
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_code(movie_code)
        if not movie:
            await message.answer(_("movie_not_found", lang))
        else:
            await deliver_movie(message, movie, user, lang, session, bot)
        return

    # 3. Language selection for new users
    if is_new or not user.language:
        await message.answer(
            _("welcome_new", lang),
            reply_markup=language_select_kb(),
        )
        return

    # 4. Deliver pending movie if any
    if user.pending_movie_code:
        code = user.pending_movie_code
        await user_svc.set_pending_movie(user_id, None)
        movie_svc = MovieService(session)
        movie = await movie_svc.get_by_code(code)
        if movie:
            await deliver_movie(message, movie, user, lang, session, bot)
            return

    # 5. Welcome back (main menu)
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
    """Deliver movie files or episode list directly to the user (no movie details post)."""
    from bot.services.movie_service import MovieService
    from bot.handlers.user.callbacks import _send_version
    from bot.keyboards.user import episode_select_kb

    movie_svc = MovieService(session)
    await movie_svc.increment_views(movie.id)

    if movie.movie_type in ("film", "multfilm"):
        active_versions = await movie_svc.get_active_versions(movie.id)
        if not active_versions:
            await message.answer(_("movie_no_versions", lang))
            return
        
        # Direct send all active versions
        for version in active_versions:
            await _send_version(message, version, user, lang, movie.id, session, bot)
            
    elif movie.movie_type in ("serial", "anime"):
        if movie.serial_link:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from bot.config import settings
            
            title = movie.title_uz or movie.title_original
            caption = f"🎬 <b>{title}</b> serialining barcha qismlari joylashgan kanal:\n\n👇 Ko'rish uchun pastdagi tugmani bosing."
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍿 Ko'rish", url=movie.serial_link)],
                [InlineKeyboardButton(text="Kinoni uzatish", url=f"https://t.me/{settings.BOT_USERNAME.strip('@')}?start=movie_{movie.code}")]
            ])
            await message.answer(caption, reply_markup=kb, parse_mode="HTML")
            return

        if not movie.episodes:
            await message.answer("⚠️ Ushbu serial/anime uchun hali qismlar yuklanmagan.")
            return
        await message.answer(
            _("choose_episode", lang),
            reply_markup=episode_select_kb(movie.episodes, lang),
        )

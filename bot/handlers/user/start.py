import io
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.movie_service import MovieService
from bot.services.subscription_service import SubscriptionService
from bot.keyboards.user import main_menu_kb
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
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = cb.from_user.id
    user_svc = UserService(session)
    user = await user_svc.get(user_id)
    lang = user.language if user else "uz"

    sub_svc = SubscriptionService(session, bot)
    is_vip = await user_svc.is_vip(user_id)
    not_subscribed = [] if is_vip else await sub_svc.get_unsubscribed_channels(user_id)

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
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "go_main_menu")
async def go_main_menu(cb: CallbackQuery, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    await cb.message.answer(
        _("welcome_back", lang),
        reply_markup=main_menu_kb(),
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
    """Deliver movie file directly to the user."""
    from bot.services.ad_service import AdService
    from bot.keyboards.user import vip_required_kb
    from bot.utils.i18n import get_video_caption
    
    user_svc = UserService(session)
    movie_svc = MovieService(session)
    
    # VIP check
    if movie.is_vip and not await user_svc.is_vip(user.id):
        await message.answer(
            _("vip_required", lang),
            reply_markup=vip_required_kb(),
        )
        return

    # Download limit check
    if not await user_svc.check_download_limit(user.id):
        await message.answer(
            _("download_limit", lang),
            reply_markup=vip_required_kb(),
        )
        return

    await movie_svc.increment_views(movie.id)

    # If it is serial and has a serial link
    if movie.movie_type in ("serial", "anime") and movie.serial_link:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        title = movie.title or movie.title_original
        caption = f"🎬 <b>{title}</b> serialining barcha qismlari joylashgan kanal:\n\n👇 Ko'rish uchun pastdagi tugmani bosing."
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍿 Ko'rish", url=movie.serial_link)],
            [InlineKeyboardButton(text="Kinoni uzatish", url=f"https://t.me/{settings.BOT_USERNAME.strip('@')}?start=movie_{movie.code}")]
        ])
        await message.answer(caption, reply_markup=kb, parse_mode="HTML")
        return

    if not movie.file_id and not movie.database_message_id:
        await message.answer(_("movie_no_versions", lang))
        return

    caption = get_video_caption(
        movie=movie,
        lang=lang,
        bot_username=settings.BOT_USERNAME,
        channel_username=settings.PUBLIC_CHANNEL_USERNAME,
    )

    # Download poster for thumbnail
    poster_id = movie.poster_file_id
    thumb = None
    if poster_id:
        try:
            file_info = await bot.get_file(poster_id)
            if file_info.file_path:
                dest = io.BytesIO()
                await bot.download_file(file_info.file_path, dest)
                dest.seek(0)
                thumb = BufferedInputFile(dest.read(), filename="thumb.jpg")
        except Exception:
            pass

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    share_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Kinoni uzatish",
            url=f"https://t.me/{settings.BOT_USERNAME.strip('@')}?start=movie_{movie.code}"
        )]
    ])

    if movie.database_message_id and settings.DATABASE_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=user.id,
                from_chat_id=settings.DATABASE_CHANNEL_ID,
                message_id=movie.database_message_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=share_kb,
            )
        except Exception:
            if movie.file_id:
                await message.answer_video(
                    video=movie.file_id,
                    caption=caption,
                    thumbnail=thumb,
                    parse_mode="HTML",
                    reply_markup=share_kb,
                )
            else:
                await message.answer(_("movie_no_versions", lang))
    else:
        if movie.file_id:
            await message.answer_video(
                video=movie.file_id,
                caption=caption,
                thumbnail=thumb,
                parse_mode="HTML",
                reply_markup=share_kb,
            )
        else:
            await message.answer(_("movie_no_versions", lang))

    await user_svc.increment_downloads(user.id)
    await movie_svc.log_download(user.id, movie.id)

    # Show ad for non-VIP users
    if not await user_svc.is_vip(user.id):
        ad_svc = AdService(session)
        ad = await ad_svc.get_random_ad()
        if ad and ad.show_after_download:
            from bot.handlers.user.callbacks import _send_ad
            await _send_ad(message, ad)

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.keyboards.user import back_to_menu_kb
from bot.utils.i18n import _
from bot.config import settings
from datetime import datetime

router = Router()


@router.callback_query(F.data == "menu_settings")
async def show_settings_cb(cb: CallbackQuery, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)

    vip_status = "✅ Faol" if user and user.is_vip else "❌ Faol emas"
    if user and user.is_vip and user.vip_until:
        until = user.vip_until.strftime("%d.%m.%Y")
        vip_status += f" ({until} gacha)"

    downloads_today = await user_svc.get_downloads_today(cb.from_user.id)
    limit = settings.VIP_DAILY_LIMIT if (user and user.is_vip) else settings.DAILY_DOWNLOAD_LIMIT

    text = _("settings_info", "uz",
             name=user.full_name if user else "",
             vip_status=vip_status,
             downloads=downloads_today,
             limit=limit)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_main_menu")],
    ])

    await cb.message.answer(text, reply_markup=kb)
    await cb.answer()


async def _build_settings_text(user_id: int, session) -> tuple:
    user_svc = UserService(session)
    user = await user_svc.get(user_id)
    
    vip_status = "✅ Faol" if user and user.is_vip else "❌ Faol emas"
    if user and user.is_vip and user.vip_until:
        until = user.vip_until.strftime("%d.%m.%Y")
        vip_status += f" ({until} gacha)"
        
    downloads_today = await user_svc.get_downloads_today(user_id)
    limit = settings.VIP_DAILY_LIMIT if (user and user.is_vip) else settings.DAILY_DOWNLOAD_LIMIT
    
    text = _("settings_info", "uz",
             name=user.full_name if user else "",
             vip_status=vip_status,
             downloads=downloads_today,
             limit=limit)
             
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_main_menu")],
    ])
    return text, kb


@router.message(F.text.in_([
    "⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"
]))
async def show_settings_msg(message: Message, session: AsyncSession):
    text, kb = await _build_settings_text(message.from_user.id, session)
    await message.answer(text, reply_markup=kb)

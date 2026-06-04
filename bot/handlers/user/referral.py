from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.keyboards.user import back_to_menu_kb
from bot.utils.i18n import _
from bot.config import settings

router = Router()


@router.callback_query(F.data == "menu_referral")
async def show_referral(cb: CallbackQuery, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    count = await user_svc.get_referral_count(cb.from_user.id)
    ref_code = user.referral_code if user else ""
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{cb.from_user.id}"

    text = _("referral_info", lang, count=count, link=ref_link)
    await cb.message.answer(text, reply_markup=back_to_menu_kb(lang))
    await cb.answer()

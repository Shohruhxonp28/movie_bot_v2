from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.vip_service import VIPService
from bot.keyboards.user import back_to_menu_kb
from bot.utils.i18n import _

router = Router()


@router.callback_query(F.data == "menu_vip")
async def show_vip(cb: CallbackQuery, session: AsyncSession):
    user_svc = UserService(session)
    vip_svc = VIPService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    plans = await vip_svc.get_plans()
    text = _("vip_info", lang)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for plan in plans:
        plan_name = getattr(plan, f"name_{lang}", plan.name_uz)
        price_label = f"{plan.price:,.0f} so'm" if lang == "uz" else f"{plan.price:,.0f} руб" if lang == "ru" else f"${plan.price:,.0f}"
        buttons.append([InlineKeyboardButton(
            text=f"💎 {plan_name} — {price_label}",
            callback_data=f"vip_plan_{plan.id}",
        )])

    if not plans:
        no_plans = {
            "uz": "Hozircha VIP rejalari mavjud emas. Admin bilan bog'laning.",
            "ru": "VIP планы пока не доступны. Свяжитесь с администратором.",
            "en": "No VIP plans available yet. Contact admin.",
        }
        text = no_plans.get(lang, no_plans["uz"])

    buttons.append([InlineKeyboardButton(text=_("btn_menu", lang), callback_data="go_main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await cb.message.answer(text, reply_markup=kb)
    await cb.answer()

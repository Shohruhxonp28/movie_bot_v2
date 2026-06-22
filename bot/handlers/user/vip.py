from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, PhotoSize,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.vip_service import VIPService
from bot.keyboards.user import back_to_menu_kb, main_menu_kb
from bot.utils.i18n import _
from bot.config import settings
from bot.utils.logger import logger

router = Router()


class VIPCheckState(StatesGroup):
    waiting_check = State()


# ─── Helpers ─────────────────────────────────────────────────────────────────

import random
import string

def _price_label(plan, lang: str) -> str:
    # Use space as thousands separator for UZ
    formatted_price = f"{plan.price:,.0f}".replace(",", " ")
    if lang == "ru":
        return f"{formatted_price} руб"
    elif lang == "en":
        return f"${formatted_price}"
    return f"{formatted_price} so'm"


def _generate_payment_id(length=16):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


async def _build_vip_menu(user_id: int, session: AsyncSession):
    user_svc = UserService(session)
    vip_svc = VIPService(session)
    user = await user_svc.get(user_id)
    lang = user.language if user else "uz"
    plans = await vip_svc.get_plans()
    text = _("vip_info", lang)
    buttons = []
    for plan in plans:
        plan_name = getattr(plan, f"name_{lang}", plan.name_uz)
        buttons.append([InlineKeyboardButton(
            text=f"👇 {plan_name} — {_price_label(plan, lang)}",
            callback_data=f"vip_plan_{plan.id}",
        )])
    if not plans:
        no_plans = {
            "uz": "Hozircha VIP rejalari mavjud emas. Admin bilan bog'laning.",
            "ru": "VIP планы пока не доступны. Свяжитесь с администратором.",
            "en": "No VIP plans available yet. Contact admin.",
        }
        text = no_plans.get(lang, no_plans["uz"])
    buttons.append([InlineKeyboardButton(text=_("btn_back", lang), callback_data="go_main_menu")])
    return text, InlineKeyboardMarkup(inline_keyboard=buttons), lang


# ─── Show VIP Menu ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_vip")
async def show_vip_cb(cb: CallbackQuery, session: AsyncSession):
    logger.info(f"User {cb.from_user.id} requested VIP menu (callback)")
    text, kb, _ = await _build_vip_menu(cb.from_user.id, session)
    
    try:
        if cb.message.photo:
            await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
            await cb.message.delete()
        else:
            await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error showing VIP menu (callback): {e}")
        await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
    
    await cb.answer()


@router.message(F.text.in_([
    "💎 VIP obuna", "💎 VIP подписка", "💎 VIP subscription"
]))
async def show_vip_msg(message: Message, session: AsyncSession):
    logger.info(f"User {message.from_user.id} requested VIP menu (text)")
    text, kb, _ = await _build_vip_menu(message.from_user.id, session)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ─── Plan Selected → Show Payment Details ─────────────────────────────────────

@router.callback_query(F.data.startswith("vip_plan_"))
async def vip_plan_selected(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])
    vip_svc = VIPService(session)
    user_svc = UserService(session)

    plan = await vip_svc.get_plan(plan_id)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    if not plan:
        await cb.answer("Plan topilmadi", show_alert=True)
        return

    plan_name = getattr(plan, f"name_{lang}", plan.name_uz)
    price = _price_label(plan, lang)
    card = settings.PAYMENT_CARD or "5614 6818 7277 3647"
    payment_id = _generate_payment_id()

    payment_texts = {
        "uz": (
            f"✅ <b>To'lov so'rovi yaratildi!</b>\n\n"
            f"💎 Tarif: <b>{plan_name}</b>\n"
            f"📅 Davomiyligi: <b>{plan.duration_days} kun</b>\n"
            f"🆔 To'lov: <code>{payment_id}</code>\n"
            f"💵 Summa: <b>{price}</b>\n\n"
            f"💳 Karta: <code>{card}</code>\n"
            f"<i>Karta raqamni nusxalab to'lov qiling.</i>\n\n"
            f"⚠️ <b>O'QIMASDAN PUL TASHLAMANG!</b>\n\n"
            f"Pastdagi faqat pulni {price} tashlamang, "
            f"faqat kopirovat orqali qancha pul bo'lsa o'shani tashlang.\n"
            f"Agar pulingiz tushmay qolsa, adminga (@brent_111) chekni tashlang, sizga VIP qilib beradi."
        ),
        "ru": (
            f"✅ <b>Запрос на оплату создан!</b>\n\n"
            f"💎 Тариф: <b>{plan_name}</b>\n"
            f"📅 Длительность: <b>{plan.duration_days} дней</b>\n"
            f"🆔 Оплата: <code>{payment_id}</code>\n"
            f"💵 Сумма: <b>{price}</b>\n\n"
            f"💳 Карта: <code>{card}</code>\n"
            f"<i>Скопируйте номер карты и произведите оплату.</i>\n\n"
            f"⚠️ <b>НЕ ОТПRAWЛЯЙТЕ ДЕНЬГИ БЕЗ ЧТЕНИЯ!</b>\n\n"
            f"Отправляйте именно ту сумму, которая указана ({price}), "
            f"лучше всего скопируйте её.\n"
            f"Если оплата не прошла, отправьте чек админу (@brent_111)."
        ),
        "en": (
            f"✅ <b>Payment request created!</b>\n\n"
            f"💎 Plan: <b>{plan_name}</b>\n"
            f"📅 Duration: <b>{plan.duration_days} days</b>\n"
            f"🆔 Payment: <code>{payment_id}</code>\n"
            f"💵 Amount: <b>{price}</b>\n\n"
            f"💳 Card: <code>{card}</code>\n"
            f"<i>Copy the card number and make the payment.</i>\n\n"
            f"⚠️ <b>DO NOT SEND MONEY WITHOUT READING!</b>\n\n"
            f"Send exactly the amount specified ({price}), "
            f"copy it to be sure.\n"
            f"If payment fails, send the receipt to admin (@brent_111)."
        ),
    }

    buttons = [
        [InlineKeyboardButton(text="🟣 Kvitansiya", url="https://t.me/brent_111")], # Placeholder for receipt link or similar
        [InlineKeyboardButton(text=f"📋 Summani nusxalash: {price}", callback_data=f"copy_price_{plan.price}")],
        [InlineKeyboardButton(text=f"📋 Kartani nusxalash: {card}", callback_data=f"copy_card_{card}")],
        [InlineKeyboardButton(text="🔄 To'lovni tekshirish", callback_data=f"vip_send_check_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_vip")]
    ]

    await cb.message.edit_text(
        payment_texts.get(lang, payment_texts["uz"]),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("copy_price_"))
async def copy_price_cb(cb: CallbackQuery):
    price = cb.data.split("_")[-1]
    # format price with space for display in alert
    try:
        f_price = f"{float(price):,.0f}".replace(",", " ")
    except:
        f_price = price
    await cb.answer(f"Summa: {f_price} so'm. Uni xabardagi kodni bosib nusxalab oling.", show_alert=True)


@router.callback_query(F.data.startswith("copy_card_"))
async def copy_card_cb(cb: CallbackQuery):
    card = cb.data.split("_")[-1]
    await cb.answer(f"Karta: {card}. Uni xabardagi kodni bosib nusxalab oling.", show_alert=True)


# ─── User Ready to Send Check ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vip_send_check_"))
async def vip_send_check_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    await state.set_state(VIPCheckState.waiting_check)
    await state.update_data(plan_id=plan_id, lang=lang)

    prompt = {
        "uz": "📸 Iltimos, to'lov cheki rasmini yuboring (screenshot yoki foto):",
        "ru": "📸 Пожалуйста, отправьте фото чека об оплате:",
        "en": "📸 Please send a photo of the payment receipt:",
    }

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("btn_back", lang), callback_data=f"vip_plan_{plan_id}")]
    ])
    await cb.message.answer(prompt.get(lang, prompt["uz"]), reply_markup=cancel_kb)
    await cb.answer()


# ─── Receive Check Photo → Forward to Admin Group ─────────────────────────────

@router.message(VIPCheckState.waiting_check, F.photo)
async def vip_check_received(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    plan_id = data.get("plan_id")
    lang = data.get("lang", "uz")

    user_svc = UserService(session)
    vip_svc = VIPService(session)

    user = await user_svc.get(message.from_user.id)
    plan = await vip_svc.get_plan(plan_id)

    plan_name = getattr(plan, f"name_{lang}", plan.name_uz) if plan else "Noma'lum"
    price = _price_label(plan, lang) if plan else "—"
    days = plan.duration_days if plan else "?"

    user_mention = f"@{user.username}" if (user and user.username) else f"ID: {message.from_user.id}"
    full_name = (user.full_name if user else None) or message.from_user.full_name or ""

    admin_caption = (
        f"💳 <b>Yangi to'lov cheki!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b> ({user_mention})\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💎 Plan: <b>{plan_name}</b> — {price}\n"
        f"⏳ Muddat: <b>{days} kun</b>"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"adm_approve_vip_{message.from_user.id}_{plan_id}",
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"adm_reject_vip_{message.from_user.id}",
            ),
        ]
    ])

    photo: PhotoSize = message.photo[-1]

    # Determine targets: group + all individual admins
    group_id = settings.ADMIN_GROUP_ID
    # Ignore placeholder value
    if group_id and group_id.strip() in ("", "-1001234567890", "0"):
        group_id = ""

    group_sent = False

    # 1. Try to send to admin group
    if group_id:
        try:
            await bot.send_photo(
                chat_id=int(group_id),
                photo=photo.file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_kb,
            )
            group_sent = True
            logger.info(f"VIP check forwarded to admin group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send check to admin group {group_id}: {e}")

    # 2. Always send to individual admins (regardless of group)
    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_kb,
            )
            logger.info(f"VIP check forwarded to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send check to admin {admin_id}: {e}")

    # Confirm to user
    confirm_texts = {
        "uz": "✅ Chekingiz yuborildi! Admin tekshirib, VIP faollashtiriladi.",
        "ru": "✅ Ваш чек отправлен! Администратор проверит и активирует VIP.",
        "en": "✅ Your receipt has been sent! Admin will verify and activate VIP.",
    }
    await message.answer(
        confirm_texts.get(lang, confirm_texts["uz"]),
        reply_markup=main_menu_kb(lang),
    )
    await state.clear()


@router.message(VIPCheckState.waiting_check)
async def vip_check_wrong_type(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    texts = {
        "uz": "❌ Iltimos, faqat rasm (foto) yuboring.",
        "ru": "❌ Пожалуйста, отправьте только фото.",
        "en": "❌ Please send a photo only.",
    }
    await message.answer(texts.get(lang, texts["uz"]))


# ─── Admin Approve ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_approve_vip_"))
async def adm_approve_vip(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    # Format: adm_approve_vip_{user_id}_{plan_id}
    parts = cb.data.split("_")
    try:
        user_id = int(parts[3])
        plan_id = int(parts[4]) if len(parts) > 4 else None
    except (IndexError, ValueError):
        await cb.answer("Xatolik", show_alert=True)
        return

    vip_svc = VIPService(session)
    user_svc = UserService(session)

    plan = await vip_svc.get_plan(plan_id) if plan_id else None
    days = plan.duration_days if plan else 30

    await vip_svc.grant_vip(user_id, days, plan_id=plan_id, granted_by=cb.from_user.id)

    user = await user_svc.get(user_id)
    lang = user.language if user else "uz"

    notify = {
        "uz": f"🎉 VIP obunangiz tasdiqlandi! <b>{days} kun</b> davomida VIP maqomida bo'lasiz.",
        "ru": f"🎉 Ваша VIP подписка подтверждена! VIP статус активен <b>{days} дней</b>.",
        "en": f"🎉 Your VIP subscription is confirmed! You have VIP for <b>{days} days</b>.",
    }
    try:
        await bot.send_message(user_id, notify.get(lang, notify["uz"]), parse_mode="HTML")
    except Exception:
        pass

    approver = cb.from_user.username or str(cb.from_user.id)
    try:
        await cb.message.edit_caption(
            (cb.message.caption or "") + f"\n\n✅ <b>Tasdiqlandi</b> — @{approver}",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await cb.answer("✅ VIP berildi!", show_alert=True)


# ─── Admin Reject ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_reject_vip_"))
async def adm_reject_vip(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    # Format: adm_reject_vip_{user_id}
    parts = cb.data.split("_")
    try:
        user_id = int(parts[3])
    except (IndexError, ValueError):
        await cb.answer("Xatolik", show_alert=True)
        return

    user_svc = UserService(session)
    user = await user_svc.get(user_id)
    lang = user.language if user else "uz"

    notify = {
        "uz": "❌ To'lovingiz tasdiqlanmadi. Chekni qayta tekshirib, admin bilan bog'laning.",
        "ru": "❌ Ваш платёж не подтверждён. Проверьте чек и свяжитесь с администратором.",
        "en": "❌ Your payment was not confirmed. Please recheck and contact admin.",
    }
    try:
        await bot.send_message(user_id, notify.get(lang, notify["uz"]))
    except Exception:
        pass

    rejecter = cb.from_user.username or str(cb.from_user.id)
    try:
        await cb.message.edit_caption(
            (cb.message.caption or "") + f"\n\n❌ <b>Rad etildi</b> — @{rejecter}",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await cb.answer("❌ Rad etildi", show_alert=True)

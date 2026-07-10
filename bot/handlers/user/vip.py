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
from bot.keyboards.user import main_menu_kb
from bot.utils.i18n import _
from bot.config import settings
from bot.utils.logger import logger
import random
import string

router = Router()


class VIPCheckState(StatesGroup):
    waiting_check = State()


def _price_label(plan) -> str:
    formatted_price = f"{plan.price:,.0f}".replace(",", " ")
    return f"{formatted_price} so'm"


def _generate_payment_id(length=16):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


async def _build_vip_menu(user_id: int, session: AsyncSession):
    user_svc = UserService(session)
    vip_svc = VIPService(session)
    plans = await vip_svc.get_plans()
    text = _("vip_info", "uz")
    buttons = []
    for plan in plans:
        buttons.append([InlineKeyboardButton(
            text=f"👇 {plan.name} — {_price_label(plan)}",
            callback_data=f"vip_plan_{plan.id}",
        )])
    if not plans:
        text = "Hozircha VIP rejalari mavjud emas. Admin bilan bog'laning."
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="go_main_menu")])
    return text, InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "menu_vip")
async def show_vip_cb(cb: CallbackQuery, session: AsyncSession):
    logger.info(f"User {cb.from_user.id} requested VIP menu (callback)")
    text, kb = await _build_vip_menu(cb.from_user.id, session)
    
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
    text, kb = await _build_vip_menu(message.from_user.id, session)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("vip_plan_"))
async def vip_plan_selected(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])
    vip_svc = VIPService(session)

    plan = await vip_svc.get_plan(plan_id)
    if not plan:
        await cb.answer("Plan topilmadi", show_alert=True)
        return

    plan_name = plan.name
    price = _price_label(plan)
    card = settings.PAYMENT_CARD or "5614 6818 7277 3647"
    payment_id = _generate_payment_id()

    payment_text = (
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
        f"Agar pulingiz tushmay qolsa, adminga (@Shohruhxon_2006) chekni tashlang, sizga VIP qilib beradi."
    )

    buttons = [
        [InlineKeyboardButton(text="🟣 Kvitansiya", url="https://t.me/Shohruhxon_2006")],
        [InlineKeyboardButton(text=f"📋 Summani nusxalash: {price}", callback_data=f"copy_price_{plan.price}")],
        [InlineKeyboardButton(text=f"📋 Kartani nusxalash: {card}", callback_data=f"copy_card_{card}")],
        [InlineKeyboardButton(text="🔄 To'lovni tekshirish", callback_data=f"vip_send_check_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_vip")]
    ]

    await cb.message.edit_text(
        payment_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("copy_price_"))
async def copy_price_cb(cb: CallbackQuery):
    price = cb.data.split("_")[-1]
    try:
        f_price = f"{float(price):,.0f}".replace(",", " ")
    except:
        f_price = price
    await cb.answer(f"Summa: {f_price} so'm. Uni xabardagi kodni bosib nusxalab oling.", show_alert=True)


@router.callback_query(F.data.startswith("copy_card_"))
async def copy_card_cb(cb: CallbackQuery):
    card = cb.data.split("_")[-1]
    await cb.answer(f"Karta: {card}. Uni xabardagi kodni bosib nusxalab oling.", show_alert=True)


@router.callback_query(F.data.startswith("vip_send_check_"))
async def vip_send_check_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])

    await state.set_state(VIPCheckState.waiting_check)
    await state.update_data(plan_id=plan_id)

    prompt = "📸 Iltimos, to'lov cheki rasmini yuboring (screenshot yoki foto):"

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"vip_plan_{plan_id}")]
    ])
    await cb.message.answer(prompt, reply_markup=cancel_kb)
    await cb.answer()


@router.message(VIPCheckState.waiting_check, F.photo)
async def vip_check_received(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    plan_id = data.get("plan_id")

    user_svc = UserService(session)
    vip_svc = VIPService(session)

    user = await user_svc.get(message.from_user.id)
    plan = await vip_svc.get_plan(plan_id)

    plan_name = plan.name if plan else "Noma'lum"
    price = _price_label(plan) if plan else "—"
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
    if group_id and group_id.strip() in ("", "-1001234567890", "0"):
        group_id = ""

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
            logger.info(f"VIP check forwarded to admin group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send check to admin group {group_id}: {e}")

    # 2. Always send to individual admins
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

    await message.answer(
        "✅ Chekingiz yuborildi! Admin tekshirib, VIP faollashtiriladi.",
        reply_markup=main_menu_kb(),
    )
    await state.clear()


@router.message(VIPCheckState.waiting_check)
async def vip_check_wrong_type(message: Message):
    await message.answer("❌ Iltimos, faqat rasm (foto) yuboring.")


@router.callback_query(F.data.startswith("adm_approve_vip_"))
async def adm_approve_vip(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    parts = cb.data.split("_")
    try:
        user_id = int(parts[3])
        plan_id = int(parts[4]) if len(parts) > 4 else None
    except (IndexError, ValueError):
        await cb.answer("Xatolik", show_alert=True)
        return

    vip_svc = VIPService(session)

    plan = await vip_svc.get_plan(plan_id) if plan_id else None
    days = plan.duration_days if plan else 30

    await vip_svc.grant_vip(user_id, days, plan_id=plan_id, granted_by=cb.from_user.id)

    notify = f"🎉 VIP obunangiz tasdiqlandi! <b>{days} kun</b> davomida VIP maqomida bo'lasiz."
    try:
        await bot.send_message(user_id, notify, parse_mode="HTML")
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


@router.callback_query(F.data.startswith("adm_reject_vip_"))
async def adm_reject_vip(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    parts = cb.data.split("_")
    try:
        user_id = int(parts[3])
    except (IndexError, ValueError):
        await cb.answer("Xatolik", show_alert=True)
        return

    notify = "❌ To'lovingiz tasdiqlanmadi. Chekni qayta tekshirib, admin bilan bog'laning."
    try:
        await bot.send_message(user_id, notify)
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

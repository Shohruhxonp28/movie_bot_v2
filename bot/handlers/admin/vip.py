from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.utils.filters import IsAdmin
from bot.services.vip_service import VIPService
from bot.services.user_service import UserService
from bot.database.models import User
from bot.keyboards.admin import admin_main_kb
from datetime import datetime

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class VIPGrantState(StatesGroup):
    waiting_user_id = State()
    waiting_days = State()


class VIPRevokeState(StatesGroup):
    waiting_user_id = State()


class VIPPlanState(StatesGroup):
    waiting_name = State()
    waiting_days = State()
    waiting_price = State()


class VIPPlanEditState(StatesGroup):
    waiting_new_value = State()


@router.callback_query(F.data == "adm_vip")
async def adm_vip_menu(cb: CallbackQuery, session: AsyncSession):
    vip_svc = VIPService(session)
    plans = await vip_svc.get_plans()

    # Count VIP users
    result = await session.execute(
        select(User).where(User.is_vip == True)
    )
    vip_users_count = len(result.scalars().all())

    text = (
        f"💎 <b>VIP boshqaruvi</b>\n\n"
        f"👥 Hozirda faol VIP foydalanuvchilar: <b>{vip_users_count} ta</b>\n\n"
        f"Mavjud tariflar ro'yxati va amallar:"
    )
    
    buttons = []
    for plan in plans:
        price_lbl = f"{plan.price:,.0f}".replace(",", " ")
        buttons.append([InlineKeyboardButton(
            text=f"🎫 {plan.name} ({plan.duration_days} kun) — {price_lbl} so'm",
            callback_data=f"adm_vplan_{plan.id}"
        )])

    buttons.append([InlineKeyboardButton(text="👥 VIP foydalanuvchilar ro'yxati", callback_data="adm_vip_users_list")])
    buttons.append([InlineKeyboardButton(text="👤 VIP berish", callback_data="adm_vip_grant")])
    buttons.append([InlineKeyboardButton(text="❌ VIP bekor qilish (ID orqali)", callback_data="adm_vip_revoke")])
    buttons.append([InlineKeyboardButton(text="➕ Yangi plan", callback_data="adm_vip_newplan")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()


# ─── VIP Users List and Detail Management ─────────────────────────────────────

@router.callback_query(F.data.startswith("adm_vip_users_list"))
async def adm_vip_users_list(cb: CallbackQuery, session: AsyncSession):
    # Parse pagination if any
    parts = cb.data.split("_")
    page = 1
    if len(parts) > 4 and parts[4] == "page":
        try:
            page = int(parts[5])
        except (IndexError, ValueError):
            page = 1

    limit = 10
    offset = (page - 1) * limit

    now = datetime.now()
    result = await session.execute(
        select(User)
        .where(User.is_vip == True)
        .order_by(User.vip_until.asc())
        .limit(limit)
        .offset(offset)
    )
    vip_users = result.scalars().all()

    # Total VIP users
    total_result = await session.execute(
        select(User).where(User.is_vip == True)
    )
    total_vip = len(total_result.scalars().all())

    import math
    total_pages = math.ceil(total_vip / limit) or 1

    text = f"👥 <b>VIP foydalanuvchilar ro'yxati</b> (Jami: {total_vip}, Sahifa: {page}/{total_pages})\n\n"
    
    if not vip_users:
        text += "Hozircha VIP foydalanuvchilar mavjud emas."
    else:
        for u in vip_users:
            name = u.full_name or "Nomsiz"
            user_mention = f"@{u.username}" if u.username else f"ID: {u.id}"
            
            days_left = 0
            if u.vip_until:
                days_left = (u.vip_until - now).days
                if days_left < 0:
                    days_left = 0
                    
            text += f"• 👤 {name} ({user_mention}) — <b>{days_left} kun qoldi</b>\n"

    buttons = []
    for u in vip_users:
        name = u.full_name or str(u.id)
        user_mention = f"@{u.username}" if u.username else f"ID: {u.id}"
        buttons.append([InlineKeyboardButton(
            text=f"👤 {name[:20]} ({user_mention})",
            callback_data=f"adm_vip_udetail_{u.id}"
        )])

    # Pagination controls
    pagination_row = []
    if page > 1:
        pagination_row.append(InlineKeyboardButton(text="◀️", callback_data=f"adm_vip_users_list_page_{page - 1}"))
    pagination_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        pagination_row.append(InlineKeyboardButton(text="▶️", callback_data=f"adm_vip_users_list_page_{page + 1}"))
    buttons.append(pagination_row)

    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_vip")])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()


@router.callback_query(F.data.startswith("adm_vip_udetail_"))
async def adm_vip_user_detail(cb: CallbackQuery, session: AsyncSession):
    target_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    user = await user_svc.get(target_id)

    if not user:
        await cb.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    now = datetime.now()
    days_left = 0
    if user.vip_until:
        days_left = (user.vip_until - now).days
        if days_left < 0:
            days_left = 0

    until_str = user.vip_until.strftime("%d.%m.%Y %H:%M") if user.vip_until else "—"

    text = (
        f"👤 <b>Foydalanuvchi VIP Tafsilotlari</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Ism: <b>{user.full_name}</b>\n"
        f"🔗 Username: @{user.username or '—'}\n"
        f"📅 VIP muddati: <b>{until_str}</b>\n"
        f"⏳ Qolgan muddat: <b>{days_left} kun</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ VIP bekor qilish", callback_data=f"adm_vip_urevoke_{user.id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_vip_users_list")],
    ])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_vip_urevoke_"))
async def adm_vip_user_revoke(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    target_id = int(cb.data.split("_")[-1])
    vip_svc = VIPService(session)
    await vip_svc.revoke_vip(target_id)

    await cb.answer("❌ VIP obuna bekor qilindi", show_alert=True)

    # Notify the user
    try:
        await bot.send_message(
            target_id,
            "⚠️ <b>VIP obunangiz admin tomonidan bekor qilindi!</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass

    # Redirect to list
    await adm_vip_users_list(cb, session)


# ─── VIP Plan details ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_vplan_") & ~F.data.startswith("adm_vplan_edit_") & ~F.data.startswith("adm_vplan_delete_"))
async def adm_vip_plan_detail(cb: CallbackQuery, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])
    vip_svc = VIPService(session)
    plan = await vip_svc.get_plan(plan_id)

    if not plan:
        await cb.answer("Plan topilmadi", show_alert=True)
        return

    price_lbl = f"{plan.price:,.0f}".replace(",", " ")
    text = (
        f"💎 <b>VIP Tarif Tafsilotlari</b>\n\n"
        f"📝 Nomi: <b>{plan.name}</b>\n"
        f"📅 Davomiyligi: <b>{plan.duration_days} kun</b>\n"
        f"💰 Narxi: <b>{price_lbl} so'm</b>\n"
        f"🟢 Status: <b>{'Faol' if plan.is_active else 'Nofaol'}</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_vplan_edit_{plan.id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_vplan_delete_{plan.id}"),
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_vip")],
    ])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_vplan_delete_"))
async def adm_vip_plan_delete(cb: CallbackQuery, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])
    vip_svc = VIPService(session)
    plan = await vip_svc.get_plan(plan_id)

    if plan:
        plan.is_active = False
        await session.commit()
        await cb.answer("🗑 VIP plan o'chirildi", show_alert=True)

    await adm_vip_menu(cb, session)


@router.callback_query(F.data.startswith("adm_vplan_edit_"))
async def adm_vip_plan_edit_menu(cb: CallbackQuery, session: AsyncSession):
    plan_id = int(cb.data.split("_")[-1])
    vip_svc = VIPService(session)
    plan = await vip_svc.get_plan(plan_id)

    if not plan:
        await cb.answer("Plan topilmadi", show_alert=True)
        return

    text = f"✏️ <b>Tarifni tahrirlash</b>: <b>{plan.name}</b>\n\nQaysi maydonni o'zgartirmoqchisiz?"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nomi", callback_data=f"adm_vped_name_{plan.id}"),
            InlineKeyboardButton(text="📅 Davomiyligi (kun)", callback_data=f"adm_vped_days_{plan.id}"),
        ],
        [
            InlineKeyboardButton(text="💰 Narxi", callback_data=f"adm_vped_price_{plan.id}"),
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"adm_vplan_{plan.id}")],
    ])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_vped_"))
async def adm_vip_plan_edit_field(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")
    field = parts[2]
    plan_id = int(parts[3])

    await state.set_state(VIPPlanEditState.waiting_new_value)
    await state.update_data(plan_id=plan_id, field=field)

    prompts = {
        "name": "📝 Yangi plan nomini yozing:",
        "days": "📅 Yangi davomiyligini (kunlarda, masalan: 30) yozing:",
        "price": "💰 Yangi narxini (so'm, masalan: 60000) yozing:",
    }

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"adm_vplan_edit_{plan_id}")]
    ])

    await cb.message.edit_text(prompts.get(field, "Yozing:"), reply_markup=back_kb)
    await cb.answer()


@router.message(VIPPlanEditState.waiting_new_value)
async def adm_vip_plan_edit_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await state.clear()

    plan_id = data["plan_id"]
    field = data["field"]

    vip_svc = VIPService(session)
    plan = await vip_svc.get_plan(plan_id)

    if not plan:
        await message.answer("Tarif topilmadi.")
        return

    val = message.text.strip()
    if field == "name":
        plan.name = val
    elif field == "days":
        if not val.isdigit():
            await message.answer("❌ Kunlar soni faqat raqam bo'lishi kerak.")
            return
        plan.duration_days = int(val)
    elif field == "price":
        try:
            plan.price = float(val)
        except ValueError:
            await message.answer("❌ To'g'ri narx yozing.")
            return

    await session.commit()
    await message.answer("✅ VIP plan muvaffaqiyatli tahrirlandi!", reply_markup=admin_main_kb())

    price_lbl = f"{plan.price:,.0f}".replace(",", " ")
    text = (
        f"💎 <b>VIP Tarif Tafsilotlari</b>\n\n"
        f"📝 Nomi: <b>{plan.name}</b>\n"
        f"📅 Davomiyligi: <b>{plan.duration_days} kun</b>\n"
        f"💰 Narxi: <b>{price_lbl} so'm</b>\n"
        f"🟢 Status: <b>{'Faol' if plan.is_active else 'Nofaol'}</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_vplan_edit_{plan.id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_vplan_delete_{plan.id}"),
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_vip")],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


# ─── VIP Granting ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_vip_grant")
async def adm_vip_grant_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPGrantState.waiting_user_id)
    await cb.message.answer("👤 Foydalanuvchi ID sini yozing:\n\n❌ Bekor qilish uchun /cancel deb yozing.")
    await cb.answer()


@router.message(VIPGrantState.waiting_user_id)
async def adm_vip_grant_user(message: Message, state: FSMContext):
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam yozing.")
        return
    await state.update_data(target_user_id=int(message.text.strip()))
    await state.set_state(VIPGrantState.waiting_days)
    await message.answer("📅 Necha kun VIP berish? (masalan: 30):\n\n❌ Bekor qilish uchun /cancel deb yozing.")


@router.message(VIPGrantState.waiting_days)
async def adm_vip_grant_days(message: Message, state: FSMContext, session: AsyncSession, bot=None):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yozing.")
        return
    days = int(message.text.strip())
    data = await state.get_data()
    target_id = data["target_user_id"]

    vip_svc = VIPService(session)
    await vip_svc.grant_vip(target_id, days, granted_by=message.from_user.id)

    await message.answer(
        f"✅ Foydalanuvchi {target_id} ga {days} kunlik VIP berildi!",
        reply_markup=admin_main_kb(),
    )
    await state.clear()

    try:
        from bot.loader import bot as b
        notify = f"🎉 Sizga {days} kunlik VIP obuna berildi!"
        await b.send_message(target_id, notify)
    except Exception:
        pass


# ─── VIP Revoking by ID ───────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_vip_revoke")
async def adm_vip_revoke_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPRevokeState.waiting_user_id)
    await cb.message.answer("👤 VIP bekor qilish uchun foydalanuvchi ID sini yozing:\n\n❌ Bekor qilish uchun /cancel deb yozing.")
    await cb.answer()


@router.message(VIPRevokeState.waiting_user_id)
async def adm_vip_revoke_user(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam yozing.")
        return
    
    target_id = int(message.text.strip())
    await state.clear()

    vip_svc = VIPService(session)
    await vip_svc.revoke_vip(target_id)

    await message.answer(
        f"❌ Foydalanuvchi {target_id} dan VIP obuna olib tashlandi!",
        reply_markup=admin_main_kb(),
    )

    try:
        await bot.send_message(
            target_id,
            "⚠️ <b>VIP obunangiz bekor qilindi!</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ─── VIP Plan Creation ────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_vip_newplan")
async def adm_vip_newplan_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPPlanState.waiting_name)
    await cb.message.answer("📝 Plan nomini yozing:\n\n❌ Bekor qilish uchun /cancel deb yozing.")
    await cb.answer()


@router.message(VIPPlanState.waiting_name)
async def adm_vip_plan_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(VIPPlanState.waiting_days)
    await message.answer("📅 Necha kun? (masalan: 30):\n\n❌ Bekor qilish uchun /cancel deb yozing.")


@router.message(VIPPlanState.waiting_days)
async def adm_vip_plan_days(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Raqam yozing.")
        return
    await state.update_data(days=int(message.text.strip()))
    await state.set_state(VIPPlanState.waiting_price)
    await message.answer("💰 Narxini yozing (so'm, masalan: 50000):\n\n❌ Bekor qilish uchun /cancel deb yozing.")


@router.message(VIPPlanState.waiting_price)
async def adm_vip_plan_price(message: Message, state: FSMContext, session: AsyncSession):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ To'g'ri narx yozing.")
        return

    data = await state.get_data()
    vip_svc = VIPService(session)
    plan = await vip_svc.create_plan(
        name=data["name"],
        duration_days=data["days"],
        price=price,
    )

    await message.answer(
        f"✅ VIP plan yaratildi:\n{plan.name} — {plan.price:,.0f} so'm — {plan.duration_days} kun",
        reply_markup=admin_main_kb(),
    )
    await state.clear()

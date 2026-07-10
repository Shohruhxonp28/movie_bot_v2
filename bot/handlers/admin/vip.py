from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.vip_service import VIPService
from bot.services.user_service import UserService
from bot.keyboards.admin import admin_main_kb

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class VIPGrantState(StatesGroup):
    waiting_user_id = State()
    waiting_days = State()


class VIPPlanState(StatesGroup):
    waiting_name = State()
    waiting_days = State()
    waiting_price = State()


class VIPPlanEditState(StatesGroup):
    waiting_new_value = State()


async def _price_label(plan) -> str:
    formatted_price = f"{plan.price:,.0f}".replace(",", " ")
    return f"{formatted_price} so'm"


@router.callback_query(F.data == "adm_vip")
async def adm_vip_menu(cb: CallbackQuery, session: AsyncSession):
    vip_svc = VIPService(session)
    plans = await vip_svc.get_plans()

    text = "💎 <b>VIP boshqaruvi</b>\n\nMavjud planlar ro'yxati va amallar:"
    
    buttons = []
    # List active plans as buttons
    for plan in plans:
        price_lbl = f"{plan.price:,.0f}".replace(",", " ")
        buttons.append([InlineKeyboardButton(
            text=f"🎫 {plan.name} ({plan.duration_days} kun) — {price_lbl} so'm",
            callback_data=f"adm_vplan_{plan.id}"
        )])

    buttons.append([InlineKeyboardButton(text="👤 VIP berish", callback_data="adm_vip_grant")])
    buttons.append([InlineKeyboardButton(text="❌ VIP bekor qilish", callback_data="adm_vip_revoke")])
    buttons.append([InlineKeyboardButton(text="➕ Yangi plan", callback_data="adm_vip_newplan")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])

    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()


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

    # Return to menu
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

    from bot.keyboards.admin import admin_back_kb
    # Provide back button to return to editing choices
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


@router.callback_query(F.data == "adm_vip_revoke")
async def adm_vip_revoke_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPGrantState.waiting_user_id)
    await state.update_data(action="revoke")
    await cb.message.answer("👤 VIP bekor qilish uchun foydalanuvchi ID sini yozing:\n\n❌ Bekor qilish uchun /cancel deb yozing.")
    await cb.answer()


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

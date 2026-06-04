from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.vip_service import VIPService
from bot.services.user_service import UserService
from bot.keyboards.admin import admin_vip_actions_kb, admin_main_kb

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


@router.callback_query(F.data == "adm_vip")
async def adm_vip_menu(cb: CallbackQuery):
    await cb.message.edit_text("💎 VIP boshqaruvi:", reply_markup=admin_vip_actions_kb())
    await cb.answer()


@router.callback_query(F.data == "adm_vip_grant")
async def adm_vip_grant_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPGrantState.waiting_user_id)
    await cb.message.answer("👤 Foydalanuvchi ID sini yozing:")
    await cb.answer()


@router.message(VIPGrantState.waiting_user_id)
async def adm_vip_grant_user(message: Message, state: FSMContext):
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam yozing.")
        return
    await state.update_data(target_user_id=int(message.text.strip()))
    await state.set_state(VIPGrantState.waiting_days)
    await message.answer("📅 Necha kun VIP berish? (masalan: 30):")


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

    # Notify user
    try:
        from aiogram import Bot as AiogramBot
        from bot.loader import bot as b
        notify_map = {
            "uz": f"🎉 Sizga {days} kunlik VIP obuna berildi!",
            "ru": f"🎉 Вам выдана VIP подписка на {days} дней!",
            "en": f"🎉 You've been granted VIP for {days} days!",
        }
        user_svc = UserService(session)
        user = await user_svc.get(target_id)
        lang = user.language if user else "uz"
        await b.send_message(target_id, notify_map.get(lang, notify_map["uz"]))
    except Exception:
        pass


@router.callback_query(F.data == "adm_vip_revoke")
async def adm_vip_revoke_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPGrantState.waiting_user_id)
    await state.update_data(action="revoke")
    await cb.message.answer("👤 VIP bekor qilish uchun foydalanuvchi ID sini yozing:")
    await cb.answer()


@router.callback_query(F.data == "adm_vip_newplan")
async def adm_vip_newplan_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(VIPPlanState.waiting_name)
    await cb.message.answer("📝 Plan nomini yozing (3 tilda, | bilan ajrating, masalan: 1 oylik|1 месяц|1 month):")
    await cb.answer()


@router.message(VIPPlanState.waiting_name)
async def adm_vip_plan_name(message: Message, state: FSMContext):
    parts = message.text.strip().split("|")
    if len(parts) < 3:
        await message.answer("❌ 3 tilda yozing: uz|ru|en")
        return
    await state.update_data(names=parts)
    await state.set_state(VIPPlanState.waiting_days)
    await message.answer("📅 Necha kun? (masalan: 30):")


@router.message(VIPPlanState.waiting_days)
async def adm_vip_plan_days(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Raqam yozing.")
        return
    await state.update_data(days=int(message.text.strip()))
    await state.set_state(VIPPlanState.waiting_price)
    await message.answer("💰 Narxini yozing (so'm, masalan: 50000):")


@router.message(VIPPlanState.waiting_price)
async def adm_vip_plan_price(message: Message, state: FSMContext, session: AsyncSession):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ To'g'ri narx yozing.")
        return

    data = await state.get_data()
    names = data["names"]
    vip_svc = VIPService(session)
    plan = await vip_svc.create_plan(
        name_uz=names[0].strip(),
        name_ru=names[1].strip(),
        name_en=names[2].strip(),
        duration_days=data["days"],
        price=price,
    )

    await message.answer(
        f"✅ VIP plan yaratildi:\n{plan.name_uz} — {plan.price:,.0f} so'm — {plan.duration_days} kun",
        reply_markup=admin_main_kb(),
    )
    await state.clear()

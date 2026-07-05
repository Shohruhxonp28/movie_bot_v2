from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.services.user_service import UserService
from bot.keyboards.admin import admin_main_kb
import asyncio

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class BroadcastState(StatesGroup):
    waiting_message = State()
    confirm = State()


@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_message)
    await cb.message.answer(
        "📨 Broadcast xabari yuboring (matn, rasm yoki video).\n"
        "❌ Bekor qilish uchun /cancel yozing."
    )
    await cb.answer()


@router.message(BroadcastState.waiting_message)
async def adm_broadcast_preview(message: Message, state: FSMContext):
    # Store the exact message details for copying
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    await state.set_state(BroadcastState.confirm)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish", callback_data="adm_bc_confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="adm_bc_cancel"),
    ]])
    
    # Send a preview copy of the message back to the admin so they see exactly how it will look
    await message.copy_to(chat_id=message.from_user.id)
    await message.answer("👆 Yuqoridagi xabar barcha foydalanuvchilarga yuboriladi. Tasdiqlaysizmi?", reply_markup=kb)


@router.callback_query(F.data == "adm_bc_confirm")
async def adm_broadcast_send(cb: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")

    user_svc = UserService(session)
    user_ids = await user_svc.get_all_user_ids()

    await cb.message.answer(f"📨 Broadcast boshlandi... {len(user_ids)} foydalanuvchiga yuborilmoqda.")
    await cb.answer()
    await state.clear()

    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            success += 1
            await asyncio.sleep(0.05)  # rate limiting
        except Exception:
            failed += 1

    await cb.message.answer(
        f"✅ Broadcast tugadi!\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Muvaffaqiyatsiz: {failed}",
        reply_markup=admin_main_kb(),
    )


@router.callback_query(F.data == "adm_bc_cancel")
async def adm_broadcast_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Broadcast bekor qilindi.", reply_markup=admin_main_kb())
    await cb.answer()

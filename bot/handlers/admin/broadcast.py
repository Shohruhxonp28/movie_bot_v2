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
    # Store message info
    await state.update_data(
        msg_type="text" if message.text else "photo" if message.photo else "video",
        msg_text=message.text or message.caption or "",
        msg_file_id=(
            message.photo[-1].file_id if message.photo
            else message.video.file_id if message.video
            else None
        ),
    )
    await state.set_state(BroadcastState.confirm)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish", callback_data="adm_bc_confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="adm_bc_cancel"),
    ]])
    await message.answer("👆 Yuqoridagi xabar barcha foydalanuvchilarga yuboriladi. Tasdiqlaysizmi?", reply_markup=kb)


@router.callback_query(F.data == "adm_bc_confirm")
async def adm_broadcast_send(cb: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    user_svc = UserService(session)
    user_ids = await user_svc.get_all_user_ids()

    await cb.message.answer(f"📨 Broadcast boshlandi... {len(user_ids)} foydalanuvchi")
    await cb.answer()
    await state.clear()

    success = 0
    failed = 0

    for uid in user_ids:
        try:
            if data["msg_type"] == "text":
                await bot.send_message(uid, data["msg_text"])
            elif data["msg_type"] == "photo":
                await bot.send_photo(uid, data["msg_file_id"], caption=data["msg_text"])
            elif data["msg_type"] == "video":
                await bot.send_video(uid, data["msg_file_id"], caption=data["msg_text"])
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

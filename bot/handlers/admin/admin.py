from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.filters import IsAdmin
from bot.keyboards.admin import admin_main_kb
from bot.services.stats_service import StatsService

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Harakat bekor qilindi.", reply_markup=admin_main_kb())


@router.message(CommandStart())
async def cmd_start_admin(message: Message, state: FSMContext, session: AsyncSession, bot: Bot, command):
    await state.clear()
    # Delegate to user start handler so they get cleared of FSM and see the main menu
    from bot.handlers.user.start import cmd_start
    await cmd_start(message, command, session, bot, state)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(
        "👑 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_back")
async def adm_back(cb: CallbackQuery):
    await cb.message.edit_text(
        "👑 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "adm_stats")
async def adm_stats(cb: CallbackQuery, session: AsyncSession):
    stats_svc = StatsService(session)
    stats = await stats_svc.get_stats()

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']:,}</b>\n"
        f"💎 VIP foydalanuvchilar: <b>{stats['vip_users']:,}</b>\n"
        f"🎬 Jami kinolar: <b>{stats['total_movies']:,}</b>\n"
        f"📥 Jami yuklamalar: <b>{stats['total_downloads']:,}</b>\n"
        f"🔍 Jami qidiruvlar: <b>{stats['total_searches']:,}</b>\n"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")]
    ])
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()

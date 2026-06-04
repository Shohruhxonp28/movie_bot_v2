from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.utils.filters import IsAdmin
from bot.database.models import Channel
from bot.keyboards.admin import admin_main_kb

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddChannelState(StatesGroup):
    waiting_name = State()
    waiting_channel_id = State()
    waiting_username = State()
    waiting_invite_link = State()
    waiting_required = State()


@router.callback_query(F.data == "adm_channels")
async def adm_channels_list(cb: CallbackQuery, session: AsyncSession):
    result = await session.execute(select(Channel).where(Channel.is_active == True))
    channels = result.scalars().all()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for ch in channels:
        status = "✅" if ch.is_required else "⭕"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {ch.name}",
            callback_data=f"adm_ch_{ch.id}",
        )])
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="adm_ch_add")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])

    text = f"📢 <b>Majburiy kanallar</b> (jami: {len(channels)})"
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await cb.answer()


@router.callback_query(F.data == "adm_ch_add")
async def adm_channel_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddChannelState.waiting_name)
    await cb.message.answer("📝 Kanal nomini yozing:")
    await cb.answer()


@router.message(AddChannelState.waiting_name)
async def adm_ch_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddChannelState.waiting_channel_id)
    await message.answer("🆔 Kanal ID sini yozing (masalan: -1001234567890):")


@router.message(AddChannelState.waiting_channel_id)
async def adm_ch_id(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await state.set_state(AddChannelState.waiting_username)
    await message.answer("👤 Kanal username'ini yozing (masalan: @kanal) yoki /skip:")


@router.message(AddChannelState.waiting_username)
async def adm_ch_username(message: Message, state: FSMContext):
    username = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(username=username)
    await state.set_state(AddChannelState.waiting_invite_link)
    await message.answer("🔗 Invite link yozing yoki /skip:")


@router.message(AddChannelState.waiting_invite_link)
async def adm_ch_invite(message: Message, state: FSMContext):
    invite = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(invite_link=invite)
    await state.set_state(AddChannelState.waiting_required)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Majburiy", callback_data="adm_ch_req_yes"),
        InlineKeyboardButton(text="⭕ Ixtiyoriy", callback_data="adm_ch_req_no"),
    ]])
    await message.answer("Kanal majburiy yoki ixtiyoriy?", reply_markup=kb)


@router.callback_query(F.data.in_({"adm_ch_req_yes", "adm_ch_req_no"}))
async def adm_ch_required(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    is_required = cb.data == "adm_ch_req_yes"

    channel = Channel(
        name=data["name"],
        channel_id=data["channel_id"],
        username=data.get("username"),
        invite_link=data.get("invite_link"),
        is_required=is_required,
    )
    session.add(channel)
    await session.commit()

    await cb.message.answer(
        f"✅ Kanal qo'shildi: {data['name']}\n"
        f"{'✅ Majburiy' if is_required else '⭕ Ixtiyoriy'}",
        reply_markup=admin_main_kb(),
    )
    await state.clear()
    await cb.answer()


@router.callback_query(F.data.startswith("adm_ch_") & ~F.data.startswith("adm_ch_add") & ~F.data.startswith("adm_ch_req"))
async def adm_channel_detail(cb: CallbackQuery, session: AsyncSession):
    channel_id_str = cb.data.replace("adm_ch_", "")
    if not channel_id_str.isdigit():
        await cb.answer()
        return

    result = await session.execute(select(Channel).where(Channel.id == int(channel_id_str)))
    ch = result.scalar_one_or_none()

    if not ch:
        await cb.answer("Kanal topilmadi", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🗑 O'chirish",
            callback_data=f"adm_ch_del_{ch.id}",
        )],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_channels")],
    ])
    text = (
        f"📢 <b>{ch.name}</b>\n"
        f"🆔 {ch.channel_id}\n"
        f"👤 @{ch.username or '—'}\n"
        f"{'✅ Majburiy' if ch.is_required else '⭕ Ixtiyoriy'}"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("adm_ch_del_"))
async def adm_channel_delete(cb: CallbackQuery, session: AsyncSession):
    ch_id = int(cb.data.split("_")[-1])
    result = await session.execute(select(Channel).where(Channel.id == ch_id))
    ch = result.scalar_one_or_none()
    if ch:
        ch.is_active = False
        await session.commit()
    await cb.answer("🗑 Kanal o'chirildi", show_alert=True)
    await cb.message.edit_text("◀️ Admin panel:", reply_markup=admin_main_kb())

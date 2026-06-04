from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.utils.filters import IsAdmin
from bot.database.models import Ad
from bot.services.ad_service import AdService
from bot.keyboards.admin import admin_main_kb

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddAdState(StatesGroup):
    waiting_title = State()
    waiting_text = State()
    waiting_media = State()
    waiting_button = State()
    waiting_after_download = State()


@router.callback_query(F.data == "adm_ads")
async def adm_ads_list(cb: CallbackQuery, session: AsyncSession):
    result = await session.execute(select(Ad).where(Ad.is_active == True))
    ads = result.scalars().all()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for ad in ads:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ad.title} ({ad.impressions} ko'rishlar)",
            callback_data=f"adm_ad_{ad.id}",
        )])
    buttons.append([InlineKeyboardButton(text="➕ Reklama qo'shish", callback_data="adm_ad_add")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")])

    await cb.message.edit_text(
        f"📢 <b>Reklamalar</b> (jami: {len(ads)})",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await cb.answer()


@router.callback_query(F.data == "adm_ad_add")
async def adm_ad_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddAdState.waiting_title)
    await cb.message.answer("📝 Reklama sarlavhasini yozing:")
    await cb.answer()


@router.message(AddAdState.waiting_title)
async def adm_ad_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddAdState.waiting_text)
    await message.answer("📄 Reklama matnini yozing:")


@router.message(AddAdState.waiting_text)
async def adm_ad_text(message: Message, state: FSMContext):
    await state.update_data(ad_text=message.text.strip())
    await state.set_state(AddAdState.waiting_media)
    await message.answer("🖼 Rasm yoki video yuboring (yoki /skip):")


@router.message(AddAdState.waiting_media)
async def adm_ad_media(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "/skip":
        await state.update_data(media_file_id=None, media_type=None)
    elif message.photo:
        await state.update_data(media_file_id=message.photo[-1].file_id, media_type="photo")
    elif message.video:
        await state.update_data(media_file_id=message.video.file_id, media_type="video")
    else:
        await message.answer("/skip yozing yoki rasm/video yuboring.")
        return

    await state.set_state(AddAdState.waiting_button)
    await message.answer("🔘 Button matn|url yozing (masalan: Saytga o'tish|https://example.com) yoki /skip:")


@router.message(AddAdState.waiting_button)
async def adm_ad_button(message: Message, state: FSMContext):
    if message.text.strip() == "/skip":
        await state.update_data(button_text=None, button_url=None)
    else:
        parts = message.text.strip().split("|", 1)
        if len(parts) == 2:
            await state.update_data(button_text=parts[0].strip(), button_url=parts[1].strip())
        else:
            await message.answer("❌ Format: Matn|URL\nYoki /skip yozing.")
            return

    await state.set_state(AddAdState.waiting_after_download)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha", callback_data="adm_ad_after_yes"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="adm_ad_after_no"),
    ]])
    await message.answer("📥 Yuklash keyin ko'rsatilsinmi?", reply_markup=kb)


@router.callback_query(F.data.in_({"adm_ad_after_yes", "adm_ad_after_no"}))
async def adm_ad_after(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    ad_data = {
        "title": data["title"],
        "text": data["ad_text"],
        "media_file_id": data.get("media_file_id"),
        "media_type": data.get("media_type"),
        "button_text": data.get("button_text"),
        "button_url": data.get("button_url"),
        "show_after_download": cb.data == "adm_ad_after_yes",
    }
    ad_svc = AdService(session)
    await ad_svc.create_ad(ad_data)

    await cb.message.answer("✅ Reklama qo'shildi!", reply_markup=admin_main_kb())
    await state.clear()
    await cb.answer()

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.keyboards.user import main_menu_kb, language_select_kb
from bot.utils.i18n import _

router = Router()

VALID_LANGS = {"lang_uz": "uz", "lang_ru": "ru", "lang_en": "en"}


@router.callback_query(F.data.in_(VALID_LANGS))
async def set_language(cb: CallbackQuery, session: AsyncSession):
    lang_code = VALID_LANGS[cb.data]
    user_svc = UserService(session)
    await user_svc.set_language(cb.from_user.id, lang_code)

    changed_msg = {
        "uz": "✅ Til o'zgartirildi: O'zbekcha 🇺🇿",
        "ru": "✅ Язык изменён: Русский 🇷🇺",
        "en": "✅ Language changed: English 🇬🇧",
    }

    await cb.message.answer(
        changed_msg[lang_code] + "\n\n" + _("welcome_back", lang_code),
        reply_markup=main_menu_kb(lang_code),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "menu_language")
async def show_language_menu_cb(cb: CallbackQuery):
    await cb.message.answer(
        "🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=language_select_kb(),
    )
    await cb.answer()


@router.message(F.text.in_([
    "🌐 Tillar", "🌐 Язык", "🌐 Languages"
]))
async def show_language_menu_msg(message: Message):
    await message.answer(
        "🌐 Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=language_select_kb(),
    )

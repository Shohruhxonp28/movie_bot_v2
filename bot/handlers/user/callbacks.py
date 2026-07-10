from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.movie_service import MovieService
from bot.utils.i18n import _

router = Router()


@router.callback_query(F.data.startswith("movie_trailer_"))
async def movie_trailer(cb: CallbackQuery, session: AsyncSession):
    movie_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer(_("movie_not_found", lang), show_alert=True)
        return

    if movie.trailer_type == "video" and movie.trailer_file_id:
        await cb.message.answer_video(video=movie.trailer_file_id)
    elif movie.trailer_type == "url" and movie.trailer_url:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎬 Treyler ko'rish", url=movie.trailer_url)
        ]])
        await cb.message.answer("🎬 Treyler:", reply_markup=kb)
    else:
        await cb.answer("Treyler topilmadi", show_alert=True)
        return

    await cb.answer()


async def _send_ad(message, ad):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = None
    if ad.button_text and ad.button_url:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=ad.button_text, url=ad.button_url)
        ]])

    if ad.media_file_id and ad.media_type == "photo":
        await message.answer_photo(photo=ad.media_file_id, caption=ad.text, reply_markup=kb)
    elif ad.media_file_id and ad.media_type == "video":
        await message.answer_video(video=ad.media_file_id, caption=ad.text, reply_markup=kb)
    else:
        await message.answer(ad.text, reply_markup=kb)

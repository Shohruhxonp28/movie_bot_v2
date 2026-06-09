from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.services.user_service import UserService
from bot.services.ai_service import GeminiService
from bot.services.movie_service import MovieService
from bot.database.models import Movie
from bot.keyboards.user import ai_result_kb, back_to_menu_kb
from bot.utils.i18n import _

router = Router()


class AIState(StatesGroup):
    waiting_query = State()


@router.callback_query(F.data == "menu_ai")
async def start_ai_cb(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    await state.set_state(AIState.waiting_query)
    await state.update_data(lang=lang)
    await cb.message.answer(_("ai_prompt", lang), reply_markup=back_to_menu_kb(lang))
    await cb.answer()


@router.message(F.text.in_([
    "🤖 AI tavsiya", "🤖 AI рекомендация", "🤖 AI recommendation"
]))
async def start_ai_msg(message: Message, state: FSMContext, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(message.from_user.id)
    lang = user.language if user else "uz"

    await state.set_state(AIState.waiting_query)
    await state.update_data(lang=lang)
    await message.answer(_("ai_prompt", lang), reply_markup=back_to_menu_kb(lang))


@router.message(AIState.waiting_query)
async def process_ai_query(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    query = message.text.strip()

    thinking = await message.answer(_("ai_thinking", lang))

    # Load all active movies for AI context
    result = await session.execute(
        select(Movie).where(Movie.is_active == True).limit(100)
    )
    movies = result.scalars().all()
    movies_data = []
    for m in movies:
        title = getattr(m, f"title_{lang}", None) or m.title_original
        movies_data.append({
            "code": m.code,
            "title": title,
            "year": m.year,
            "genre": m.genre,
            "imdb_rating": m.imdb_rating,
        })

    gemini = GeminiService()

    # Determine if user is looking for recommendations or finding a specific movie
    ai_response = await gemini.recommend_movies(query, movies_data, lang)

    await thinking.delete()
    await message.answer(ai_response, reply_markup=ai_result_kb(lang))
    await state.clear()

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.user_service import UserService
from bot.services.movie_service import MovieService
from bot.services.search_service import SearchService
from bot.keyboards.user import search_results_kb, back_to_menu_kb, main_menu_kb, movies_pagination_kb
from bot.utils.i18n import _, get_movie_caption

router = Router()


@router.message(F.text == "🎬 Kinolar")
async def show_latest_movies(message: Message, session: AsyncSession):
    movie_svc = MovieService(session)
    limit = 8
    movies = await movie_svc.get_all_movies(limit=limit, offset=0)
    total_count = await movie_svc.count_movies()
    
    if not movies:
        await message.answer("🎬 Hozircha botga kinolar joylanmagan.")
        return
        
    import math
    total_pages = math.ceil(total_count / limit) or 1
    
    await message.answer(
        "🎬 Kinolar ro'yxati:",
        reply_markup=movies_pagination_kb(movies, 1, total_pages),
    )


@router.callback_query(F.data.startswith("movies_page_"))
async def process_movies_page(cb: CallbackQuery, session: AsyncSession):
    page = int(cb.data.split("_")[-1])
    
    movie_svc = MovieService(session)
    limit = 8
    offset = (page - 1) * limit
    
    movies = await movie_svc.get_all_movies(limit=limit, offset=offset)
    total_count = await movie_svc.count_movies()
    
    import math
    total_pages = math.ceil(total_count / limit) or 1
    
    try:
        await cb.message.edit_text(
            "🎬 Kinolar ro'yxati:",
            reply_markup=movies_pagination_kb(movies, page, total_pages)
        )
    except Exception:
        pass
    await cb.answer()


class SearchState(StatesGroup):
    waiting_query = State()


@router.callback_query(F.data == "menu_search")
async def start_search_cb(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"

    await state.set_state(SearchState.waiting_query)
    await state.update_data(lang=lang)
    await cb.message.answer(_("search_prompt", lang), reply_markup=back_to_menu_kb())
    await cb.answer()


@router.message(F.text.in_([
    "🔍 Qidiruv", "🔍 Поиск", "🔍 Search"
]))
async def start_search_msg(message: Message, state: FSMContext, session: AsyncSession):
    user_svc = UserService(session)
    user = await user_svc.get(message.from_user.id)
    lang = user.language if user else "uz"

    await state.set_state(SearchState.waiting_query)
    await state.update_data(lang=lang)
    await message.answer(_("search_prompt", lang), reply_markup=back_to_menu_kb())


@router.message(SearchState.waiting_query)
async def process_search(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    query = message.text.strip()

    movie_svc = MovieService(session)
    search_svc = SearchService(session)

    movies, search_type = await movie_svc.smart_search(query)
    await search_svc.log_search(message.from_user.id, query, len(movies))

    if not movies:
        await message.answer(
            _("search_not_found", lang),
            reply_markup=search_results_kb([]),
        )
        await state.clear()
        return

    if len(movies) == 1 and search_type in ("code", "exact"):
        # Direct open
        movie = movies[0]
        user_svc = UserService(session)
        user = await user_svc.get(message.from_user.id)

        from bot.handlers.user.start import deliver_movie
        await deliver_movie(message, movie, user, lang, session, bot)
    else:
        # Show list
        prefix = _("search_results", lang) if search_type == "exact" else _("search_fuzzy_results", lang)
        await message.answer(prefix, reply_markup=search_results_kb(movies))

    await state.clear()


@router.callback_query(F.data.startswith("movie_open_"))
async def open_movie_from_list(cb: CallbackQuery, session: AsyncSession, bot: Bot):
    movie_id = int(cb.data.split("_")[-1])
    user_svc = UserService(session)
    movie_svc = MovieService(session)

    user = await user_svc.get(cb.from_user.id)
    lang = user.language if user else "uz"
    movie = await movie_svc.get_by_id(movie_id)

    if not movie:
        await cb.answer(_("movie_not_found", lang), show_alert=True)
        return

    from bot.handlers.user.start import deliver_movie
    await deliver_movie(cb.message, movie, user, lang, session, bot)
    await cb.answer()

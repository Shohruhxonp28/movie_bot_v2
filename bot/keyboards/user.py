from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from bot.utils.i18n import _


def main_menu_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("btn_ai", lang)),
                KeyboardButton(text=_("btn_search", lang)),
            ],
            [
                KeyboardButton(text=_("btn_referral", lang)),
                KeyboardButton(text=_("btn_vip", lang)),
            ],
            [
                KeyboardButton(text=_("btn_language", lang)),
                KeyboardButton(text=_("btn_settings", lang)),
            ],
        ],
        resize_keyboard=True,
    )


def language_select_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ])


def back_to_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("btn_menu", lang), callback_data="go_main_menu")],
    ])


def movie_actions_kb(
    movie_id: int,
    has_trailer: bool = False,
    has_versions: bool = True,
    is_saved: bool = False,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    buttons = []
    if has_trailer:
        buttons.append([InlineKeyboardButton(
            text=_("btn_trailer", lang),
            callback_data=f"movie_trailer_{movie_id}",
        )])
    if has_versions:
        buttons.append([InlineKeyboardButton(
            text=_("btn_watch", lang),
            callback_data=f"movie_watch_{movie_id}",
        )])
    save_text = _("btn_saved", lang) if is_saved else _("btn_save", lang)
    buttons.append([InlineKeyboardButton(
        text=save_text,
        callback_data=f"movie_save_{movie_id}",
    )])
    buttons.append([InlineKeyboardButton(text=_("btn_menu", lang), callback_data="go_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def movie_versions_kb(versions, lang: str = "uz") -> InlineKeyboardMarkup:
    from bot.utils.helpers import format_version_button
    buttons = []
    for v in versions:
        buttons.append([InlineKeyboardButton(
            text=format_version_button(v, lang),
            callback_data=f"ver_{v.id}",
        )])
    buttons.append([InlineKeyboardButton(text=_("btn_back", lang), callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def episode_select_kb(episodes, lang: str = "uz") -> InlineKeyboardMarkup:
    """Show episode number buttons in rows of 5."""
    buttons = []
    row = []
    for ep in sorted(episodes, key=lambda e: e.episode_number):
        label = f"{ep.episode_number}-qism" if lang == "uz" else f"Эп. {ep.episode_number}" if lang == "ru" else f"Ep. {ep.episode_number}"
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"ep_{ep.id}",
        ))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=_("btn_back", lang), callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def episode_versions_kb(versions, lang: str = "uz") -> InlineKeyboardMarkup:
    from bot.utils.helpers import format_episode_version_button
    buttons = []
    for v in versions:
        buttons.append([InlineKeyboardButton(
            text=format_episode_version_button(v, lang),
            callback_data=f"epver_{v.id}",
        )])
    buttons.append([InlineKeyboardButton(text=_("btn_back", lang), callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subscription_kb(channels, lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        url = ch.invite_link or (f"https://t.me/{ch.username.lstrip('@')}" if ch.username else "#")
        buttons.append([InlineKeyboardButton(text=f"📢 {ch.name}", url=url)])
    buttons.append([InlineKeyboardButton(text=_("btn_check_sub", lang), callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_results_kb(movies, lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    for m in movies:
        title = getattr(m, f"title_{lang}", None) or m.title_original
        year = f" — {m.year}" if m.year else ""
        buttons.append([InlineKeyboardButton(
            text=f"🎬 {title}{year}",
            callback_data=f"movie_open_{m.id}",
        )])
    buttons.append([
        InlineKeyboardButton(text="🤖 AI bilan qidirish", callback_data="menu_ai"),
        InlineKeyboardButton(text=_("btn_menu", lang), callback_data="go_main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def vip_required_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("btn_vip_get", lang), callback_data="menu_vip")],
        [InlineKeyboardButton(text=_("btn_menu", lang), callback_data="go_main_menu")],
    ])


def ai_result_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("btn_search", lang), callback_data="menu_search")],
        [InlineKeyboardButton(text=_("btn_menu", lang), callback_data="go_main_menu")],
    ])

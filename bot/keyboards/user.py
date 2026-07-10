from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Qidiruv"),
                KeyboardButton(text="💎 VIP obuna"),
            ]
        ],
        resize_keyboard=True,
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_main_menu")],
    ])


def subscription_kb(channels) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        url = ch.invite_link or (f"https://t.me/{ch.username.lstrip('@')}" if ch.username else "#")
        buttons.append([InlineKeyboardButton(text=f"📢 {ch.name}", url=url)])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_results_kb(movies) -> InlineKeyboardMarkup:
    buttons = []
    for m in movies:
        title = m.title or m.title_original
        year = f" — {m.year}" if m.year else ""
        buttons.append([InlineKeyboardButton(
            text=f"🎬 {title}{year}",
            callback_data=f"movie_open_{m.id}",
        )])
    buttons.append([
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def vip_required_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 VIP olish", callback_data="menu_vip")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_main_menu")],
    ])


def ai_result_kb(movies=None) -> InlineKeyboardMarkup:
    buttons = []
    if movies:
        for m in movies:
            title = getattr(m, "title", None) or getattr(m, "title_original", None) or f"Kino {m.code}"
            buttons.append([InlineKeyboardButton(
                text=f"🎬 {title}",
                callback_data=f"movie_open_{m.id}"
            )])
    buttons.append([InlineKeyboardButton(text="🔍 Qidiruv", callback_data="menu_search")])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

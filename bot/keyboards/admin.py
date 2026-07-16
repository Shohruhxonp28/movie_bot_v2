from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Kinolar", callback_data="adm_movies"),
        ],
        [
            InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="adm_add_movie"),
        ],
        [
            InlineKeyboardButton(text="📺 Kanallar", callback_data="adm_channels"),
            InlineKeyboardButton(text="💎 VIP", callback_data="adm_vip"),
        ],
        [
            InlineKeyboardButton(text="📢 Reklama", callback_data="adm_ads"),
            InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats"),
        ],
        [
            InlineKeyboardButton(text="📨 Broadcast", callback_data="adm_broadcast"),
        ],
    ])


def admin_movie_confirm_kb(temp_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_confirm_{temp_id}")],
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_edit_{temp_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_cancel")],
    ])


def admin_movie_actions_kb(movie_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adm_movie_edit_{movie_id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_movie_delete_{movie_id}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_movies"),
        ],
    ])


def admin_vip_actions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 VIP berish", callback_data="adm_vip_grant")],
        [InlineKeyboardButton(text="❌ VIP bekor qilish", callback_data="adm_vip_revoke")],
        [InlineKeyboardButton(text="➕ Yangi plan", callback_data="adm_vip_newplan")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")],
    ])


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")],
    ])


def admin_yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="adm_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="adm_no"),
        ]
    ])

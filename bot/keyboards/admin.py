from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Kinolar", callback_data="adm_movies"),
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


def admin_movie_add_method_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 AI yordamida", callback_data="adm_add_ai")],
        [InlineKeyboardButton(text="✏️ Qo'lda", callback_data="adm_add_manual")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")],
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
            InlineKeyboardButton(text="🎥 Versiya qo'shish", callback_data=f"adm_addver_{movie_id}"),
            InlineKeyboardButton(text="📺 Qism qo'shish", callback_data=f"adm_addep_{movie_id}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Kanal postini yangilash", callback_data=f"adm_repost_{movie_id}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_movies"),
        ],
    ])


def admin_watermark_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="adm_wm_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="adm_wm_no"),
        ],
    ])


def admin_movie_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Film", callback_data="adm_type_film")],
        [InlineKeyboardButton(text="📺 Serial", callback_data="adm_type_serial")],
        [InlineKeyboardButton(text="🎌 Anime", callback_data="adm_type_anime")],
        [InlineKeyboardButton(text="🎠 Multfilm", callback_data="adm_type_multfilm")],
    ])


def admin_quality_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="360p", callback_data="adm_qual_360p"),
            InlineKeyboardButton(text="480p", callback_data="adm_qual_480p"),
            InlineKeyboardButton(text="720p", callback_data="adm_qual_720p"),
        ],
        [
            InlineKeyboardButton(text="1080p", callback_data="adm_qual_1080p"),
            InlineKeyboardButton(text="4K", callback_data="adm_qual_4K"),
        ],
    ])


def admin_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 Uzbek", callback_data="adm_lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Russian", callback_data="adm_lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="adm_lang_en"),
        ],
        [InlineKeyboardButton(text="🌐 Other", callback_data="adm_lang_other")],
    ])


def admin_dub_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Original", callback_data="adm_dub_original")],
        [InlineKeyboardButton(text="Professional", callback_data="adm_dub_professional")],
        [InlineKeyboardButton(text="Havaskor", callback_data="adm_dub_amateur")],
        [InlineKeyboardButton(text="Subtitr", callback_data="adm_dub_subtitle")],
    ])


def admin_premium_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Premium", callback_data="adm_prem_yes"),
            InlineKeyboardButton(text="🆓 Bepul", callback_data="adm_prem_no"),
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

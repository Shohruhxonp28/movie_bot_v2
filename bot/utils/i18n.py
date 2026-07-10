from typing import Dict, Any

TRANSLATIONS: Dict[str, str] = {
    # ─── Start / Main Menu ───────────────────────────────────────────────────
    "welcome_new": "Assalomu alaykum! Kino botga xush kelibsiz. 🎬",
    "welcome_back": (
        "Assalomu alaykum! 👋\n\n"
        "🎬 Kino botga xush kelibsiz.\n"
        "Bu bot orqali siz kino, serial, anime va multfilmlarni "
        "kod yoki nomi orqali topishingiz mumkin.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:"
    ),

    # ─── Buttons ─────────────────────────────────────────────────────────────
    "btn_search": "🔍 Qidiruv",
    "btn_vip": "💎 VIP obuna",
    "btn_language": "🌐 Tillar",
    "btn_settings": "⚙️ Sozlamalar",
    "btn_back": "◀️ Orqaga",
    "btn_menu": "🏠 Bosh menyu",
    "btn_check_sub": "✅ Tekshirish",
    "btn_trailer": "🎬 Treyler",
    "btn_watch": "📥 Ko'rish / Yuklab olish",
    "btn_vip_get": "💎 VIP olish",
    "btn_view_in_bot": "🎬 Botda ko'rish",

    # ─── Subscription ────────────────────────────────────────────────────────
    "sub_required": (
        "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
        "Obuna bo'lgandan so'ng ✅ Tekshirish tugmasini bosing."
    ),
    "sub_not_completed": "❌ Hali barcha kanallarga obuna bo'lmadingiz. Iltimos, obuna bo'ling.",

    # ─── Search ──────────────────────────────────────────────────────────────
    "search_prompt": "🔍 Kino nomi yoki kodini yuboring:",
    "search_not_found": "😕 Kino topilmadi.",
    "search_fuzzy_results": "🔎 Aniq natija topilmadi. Quyidagi o'xshash kinolardan birini tanlang:",
    "search_results": "🎬 Qidiruv natijalari:",

    # ─── Errors / Delivery ───────────────────────────────────────────────────
    "movie_not_found": "⚠️ Kino topilmadi.",
    "movie_no_versions": "⚠️ Ushbu kino yuklanmagan yoki unda fayl mavjud emas.",
    "choose_version": "📺 Sifatni tanlang:",
    "vip_required": "💎 Ushbu kinoni ko'rish uchun VIP obuna bo'lishingiz kerak.",
    "download_limit": "⚠️ Kunlik yuklab olish limitiga yetdingiz. Ko'proq yuklab olish uchun VIP obuna bo'ling.",

    # ─── Settings ────────────────────────────────────────────────────────────
    "settings_info": (
        "👤 <b>Foydalanuvchi:</b> {name}\n"
        "🌐 <b>Til:</b> O'zbekcha\n"
        "💎 <b>VIP status:</b> {vip_status}\n"
        "📥 <b>Bugungi yuklashlar:</b> {downloads} / {limit}"
    ),

    # ─── VIP ─────────────────────────────────────────────────────────────────
    "vip_info": (
        "💎 <b>VIP status afzalliklari:</b>\n\n"
        "• Reklamalarsiz foydalanish\n"
        "• Majburiy kanallarga a'zo bo'lmasdan foydalanish\n"
        "• Cheksiz yuklab olishlar\n"
        "• VIP kinolarni ko'rish imkoniyati\n\n"
        "Kerakli tarifni tanlang:"
    ),
}


def _(key: str, lang: str = "uz", **kwargs) -> str:
    """Get translation for a key (default to Uzbek)."""
    text = TRANSLATIONS.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def get_movie_caption(movie, lang: str = "uz") -> str:
    """Build movie caption in Uzbek."""
    title = movie.title or movie.title_original
    description = movie.description or ""

    lines = [f"🎬 <b>{title}</b>"]
    if movie.imdb_rating:
        lines.append(f"⭐ IMDb: <b>{movie.imdb_rating}</b>")
    if movie.year:
        lines.append(f"📅 Yil: {movie.year}")
    if movie.country:
        lines.append(f"🌍 {movie.country}")
    if movie.genre:
        lines.append(f"🎭 {movie.genre}")
    if description:
        lines.append(f"\n📝 Tavsif:\n{description[:300]}{'...' if len(description) > 300 else ''}")
    lines.append(f"\n🔎 Kod: <code>{movie.code}</code>")

    return "\n".join(lines)


def get_video_caption(movie, lang: str = "uz", bot_username: str = "", channel_username: str = "") -> str:
    """Build caption for the video file message."""
    title = movie.title or movie.title_original
    
    ch_name = channel_username.strip('@') if channel_username else "reklama_kanali"
    ch_link = f"https://t.me/{ch_name}"
    bot_link = f"https://t.me/{bot_username.strip('@')}?start=movie_{movie.code}"
    
    caption = (
        f"kino kodi : {movie.code}\n\n"
        f"🎬Kino nomi: {title}\n\n"
        f"Sizga jonli obunachilar kerakmi?\n"
        f"{ch_link}\n"
        f"reklama kanal havolasi \n"
        f"Bot havolasi: {bot_link}"
    )
    return caption

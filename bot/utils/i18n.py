from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ─── Start / Main Menu ───────────────────────────────────────────────────
    "welcome_new": {
        "uz": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "ru": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "en": "🌐 Tilni tanlang / Выберите язык / Choose language:",
    },
    "welcome_back": {
        "uz": (
            "Assalomu alaykum! 👋\n\n"
            "🎬 Kino botga xush kelibsiz.\n"
            "Bu bot orqali siz kino, serial, anime va multfilmlarni "
            "kod yoki nomi orqali topishingiz mumkin.\n\n"
            "🤖 AI yordamida sizga mos kino tavsiya olishingiz yoki "
            "nomini eslay olmayotgan kinoni topishingiz mumkin.\n\n"
            "Quyidagi menyudan kerakli bo'limni tanlang:"
        ),
        "ru": (
            "Добро пожаловать! 👋\n\n"
            "🎬 Добро пожаловать в кино бот.\n"
            "С помощью этого бота вы можете найти фильмы, сериалы, аниме и мультфильмы "
            "по коду или названию.\n\n"
            "🤖 С помощью AI вы можете получить рекомендации по фильмам "
            "или найти фильм, название которого вы не помните.\n\n"
            "Выберите нужный раздел из меню:"
        ),
        "en": (
            "Welcome! 👋\n\n"
            "🎬 Welcome to the movie bot.\n"
            "With this bot you can find movies, series, anime and cartoons "
            "by code or name.\n\n"
            "🤖 With AI you can get movie recommendations "
            "or find a movie you can't remember.\n\n"
            "Choose a section from the menu below:"
        ),
    },

    # ─── Buttons ─────────────────────────────────────────────────────────────
    "btn_ai": {"uz": "🤖 AI tavsiya", "ru": "🤖 AI рекомендация", "en": "🤖 AI recommendation"},
    "btn_search": {"uz": "🔍 Qidiruv", "ru": "🔍 Поиск", "en": "🔍 Search"},
    "btn_referral": {"uz": "👥 Referral", "ru": "👥 Рефералы", "en": "👥 Referral"},
    "btn_vip": {"uz": "💎 VIP obuna", "ru": "💎 VIP подписка", "en": "💎 VIP subscription"},
    "btn_language": {"uz": "🌐 Tillar", "ru": "🌐 Язык", "en": "🌐 Languages"},
    "btn_settings": {"uz": "⚙️ Sozlamalar", "ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    "btn_back": {"uz": "◀️ Orqaga", "ru": "◀️ Назад", "en": "◀️ Back"},
    "btn_menu": {"uz": "🏠 Bosh menyu", "ru": "🏠 Главное меню", "en": "🏠 Main menu"},
    "btn_check_sub": {"uz": "✅ Tekshirish", "ru": "✅ Проверить", "en": "✅ Check"},
    "btn_trailer": {"uz": "🎬 Treyler", "ru": "🎬 Трейлер", "en": "🎬 Trailer"},
    "btn_watch": {"uz": "📥 Ko'rish / Yuklab olish", "ru": "📥 Смотреть / Скачать", "en": "📥 Watch / Download"},
    "btn_save": {"uz": "❤️ Saqlash", "ru": "❤️ Сохранить", "en": "❤️ Save"},
    "btn_saved": {"uz": "❤️ Saqlangan", "ru": "❤️ Сохранено", "en": "❤️ Saved"},
    "btn_ai_search": {"uz": "🤖 AI bilan topish", "ru": "🤖 Найти с AI", "en": "🤖 Find with AI"},
    "btn_vip_get": {"uz": "💎 VIP olish", "ru": "💎 Получить VIP", "en": "💎 Get VIP"},
    "btn_view_in_bot": {"uz": "🎬 Botda ko'rish", "ru": "🎬 Смотреть в боте", "en": "🎬 View in bot"},

    # ─── Subscription ────────────────────────────────────────────────────────
    "sub_required": {
        "uz": (
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
            "Obuna bo'lgandan so'ng ✅ Tekshirish tugmasini bosing."
        ),
        "ru": (
            "⚠️ Для использования бота подпишитесь на следующие каналы:\n\n"
            "После подписки нажмите ✅ Проверить."
        ),
        "en": (
            "⚠️ To use the bot, subscribe to the following channels:\n\n"
            "After subscribing, press ✅ Check."
        ),
    },
    "sub_not_completed": {
        "uz": "❌ Hali barcha kanallarga obuna bo'lmadingiz. Iltimos, obuna bo'ling.",
        "ru": "❌ Вы ещё не подписаны на все каналы. Пожалуйста, подпишитесь.",
        "en": "❌ You haven't subscribed to all channels yet. Please subscribe.",
    },

    # ─── Search ──────────────────────────────────────────────────────────────
    "search_prompt": {
        "uz": "🔍 Kino nomi yoki kodini yuboring:",
        "ru": "🔍 Отправьте название фильма или код:",
        "en": "🔍 Send the movie name or code:",
    },
    "search_not_found": {
        "uz": "😕 Kino topilmadi.\n\nAI yordamida qidirib ko'rmoqchimisiz?",
        "ru": "😕 Фильм не найден.\n\nХотите поискать с помощью AI?",
        "en": "😕 Movie not found.\n\nWould you like to search with AI?",
    },
    "search_fuzzy_results": {
        "uz": "🔎 Aniq natija topilmadi. Quyidagi o'xshash kinolardan birini tanlang:",
        "ru": "🔎 Точный результат не найден. Выберите один из похожих фильмов:",
        "en": "🔎 No exact result found. Choose from similar movies below:",
    },
    "search_results": {
        "uz": "🎬 Qidiruv natijalari:",
        "ru": "🎬 Результаты поиска:",
        "en": "🎬 Search results:",
    },

    # ─── Movie ───────────────────────────────────────────────────────────────
    "movie_not_found": {
        "uz": "❌ Kino topilmadi yoki o'chirilgan.",
        "ru": "❌ Фильм не найден или удалён.",
        "en": "❌ Movie not found or deleted.",
    },
    "movie_no_versions": {
        "uz": "⚠️ Bu kino uchun hali video versiya qo'shilmagan.",
        "ru": "⚠️ Для этого фильма ещё не добавлена видеоверсия.",
        "en": "⚠️ No video version has been added for this movie yet.",
    },
    "choose_version": {
        "uz": "📺 Kerakli sifat va tilni tanlang:",
        "ru": "📺 Выберите нужное качество и язык:",
        "en": "📺 Choose the quality and language:",
    },
    "vip_required": {
        "uz": "💎 Bu versiya VIP foydalanuvchilar uchun. VIP obuna oling.",
        "ru": "💎 Эта версия только для VIP пользователей. Оформите VIP подписку.",
        "en": "💎 This version is for VIP users. Get a VIP subscription.",
    },
    "download_limit": {
        "uz": "⏳ Kunlik yuklash limitingiz tugadi. Ertaga qayta urinib ko'ring yoki VIP oling.",
        "ru": "⏳ Вы исчерпали дневной лимит загрузок. Попробуйте завтра или получите VIP.",
        "en": "⏳ You've reached your daily download limit. Try again tomorrow or get VIP.",
    },
    "movie_saved": {
        "uz": "❤️ Kino saqlandi!",
        "ru": "❤️ Фильм сохранён!",
        "en": "❤️ Movie saved!",
    },
    "movie_unsaved": {
        "uz": "💔 Kino saqlanganlardan o'chirildi.",
        "ru": "💔 Фильм удалён из сохранённых.",
        "en": "💔 Movie removed from saved.",
    },
    "choose_episode": {
        "uz": "📺 Qismni tanlang:",
        "ru": "📺 Выберите серию:",
        "en": "📺 Choose episode:",
    },

    # ─── AI ──────────────────────────────────────────────────────────────────
    "ai_prompt": {
        "uz": (
            "🤖 AI tavsiya xizmati\n\n"
            "Menga qanday kino haqida ma'lumot yuboring:\n"
            "• Janr: komediya, drama, triller...\n"
            "• Kayfiyat: qiziqarli, romantik, qo'rqinchli...\n"
            "• Mavzu: do'stlik, sevgi, urush...\n\n"
            "Yoki nomini eslay olmayotgan kinoni tavsiflang."
        ),
        "ru": (
            "🤖 AI рекомендации\n\n"
            "Расскажите мне о фильме который ищете:\n"
            "• Жанр: комедия, драма, триллер...\n"
            "• Настроение: увлекательный, романтический, страшный...\n"
            "• Тема: дружба, любовь, война...\n\n"
            "Или опишите фильм, название которого не помните."
        ),
        "en": (
            "🤖 AI Recommendations\n\n"
            "Tell me about the movie you're looking for:\n"
            "• Genre: comedy, drama, thriller...\n"
            "• Mood: exciting, romantic, scary...\n"
            "• Theme: friendship, love, war...\n\n"
            "Or describe a movie whose name you can't remember."
        ),
    },
    "ai_thinking": {
        "uz": "🤔 AI tahlil qilmoqda...",
        "ru": "🤔 AI анализирует...",
        "en": "🤔 AI is analyzing...",
    },

    # ─── VIP ─────────────────────────────────────────────────────────────────
    "vip_info": {
        "uz": (
            "💎 VIP obuna afzalliklari:\n\n"
            "✅ Cheksiz yuklash\n"
            "✅ 1080p va 4K sifatlar\n"
            "✅ Reklamasiz\n"
            "✅ Barcha premium kontentlar\n"
            "✅ AI tavsiya + ustuvorlik\n\n"
            "VIP rejalardan birini tanlang:"
        ),
        "ru": (
            "💎 Преимущества VIP подписки:\n\n"
            "✅ Неограниченные загрузки\n"
            "✅ Качество 1080p и 4K\n"
            "✅ Без рекламы\n"
            "✅ Весь премиум контент\n"
            "✅ AI рекомендации + приоритет\n\n"
            "Выберите один из VIP планов:"
        ),
        "en": (
            "💎 VIP Subscription Benefits:\n\n"
            "✅ Unlimited downloads\n"
            "✅ 1080p and 4K quality\n"
            "✅ Ad-free\n"
            "✅ All premium content\n"
            "✅ AI recommendations + priority\n\n"
            "Choose a VIP plan:"
        ),
    },

    # ─── Referral ────────────────────────────────────────────────────────────
    "referral_info": {
        "uz": (
            "👥 Referral dasturi\n\n"
            "Do'stlaringizni taklif qiling va bonus oling!\n\n"
            "📊 Sizning statistikangiz:\n"
            "👤 Taklif qilinganlar: {count}\n\n"
            "🔗 Sizning havolangiz:\n"
            "{link}"
        ),
        "ru": (
            "👥 Реферальная программа\n\n"
            "Приглашайте друзей и получайте бонусы!\n\n"
            "📊 Ваша статистика:\n"
            "👤 Приглашённые: {count}\n\n"
            "🔗 Ваша ссылка:\n"
            "{link}"
        ),
        "en": (
            "👥 Referral Program\n\n"
            "Invite friends and earn bonuses!\n\n"
            "📊 Your statistics:\n"
            "👤 Invited: {count}\n\n"
            "🔗 Your link:\n"
            "{link}"
        ),
    },

    # ─── Settings ────────────────────────────────────────────────────────────
    "settings_info": {
        "uz": (
            "⚙️ Sozlamalar\n\n"
            "👤 Ism: {name}\n"
            "🌐 Til: {language}\n"
            "💎 VIP: {vip_status}\n"
            "📥 Bugungi yuklamalar: {downloads}/{limit}"
        ),
        "ru": (
            "⚙️ Настройки\n\n"
            "👤 Имя: {name}\n"
            "🌐 Язык: {language}\n"
            "💎 VIP: {vip_status}\n"
            "📥 Загрузки сегодня: {downloads}/{limit}"
        ),
        "en": (
            "⚙️ Settings\n\n"
            "👤 Name: {name}\n"
            "🌐 Language: {language}\n"
            "💎 VIP: {vip_status}\n"
            "📥 Downloads today: {downloads}/{limit}"
        ),
    },

    # ─── Language names ───────────────────────────────────────────────────────
    "lang_uz": {"uz": "🇺🇿 O'zbekcha", "ru": "🇺🇿 O'zbekcha", "en": "🇺🇿 O'zbekcha"},
    "lang_ru": {"uz": "🇷🇺 Русский", "ru": "🇷🇺 Русский", "en": "🇷🇺 Русский"},
    "lang_en": {"uz": "🇬🇧 English", "ru": "🇬🇧 English", "en": "🇬🇧 English"},
    "language_changed": {
        "uz": "✅ Til o'zgartirildi: O'zbekcha",
        "ru": "✅ Язык изменён: Русский",
        "en": "✅ Language changed: English",
    },
}


def _(key: str, lang: str = "uz", **kwargs) -> str:
    """Get translation for a key in the given language."""
    translations = TRANSLATIONS.get(key, {})
    text = translations.get(lang, translations.get("uz", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def get_movie_caption(movie, lang: str = "uz") -> str:
    """Build movie caption in the given language."""
    title = getattr(movie, f"title_{lang}", None) or movie.title_original
    description = getattr(movie, f"description_{lang}", None) or ""

    lines = [f"🎬 <b>{title}</b>"]
    if movie.imdb_rating:
        lines.append(f"⭐ IMDb: <b>{movie.imdb_rating}</b>")
    if movie.year:
        lines.append(f"📅 Yil: {movie.year}" if lang == "uz"
                     else f"📅 Год: {movie.year}" if lang == "ru"
                     else f"📅 Year: {movie.year}")
    if movie.country:
        lines.append(f"🌍 {movie.country}")
    if movie.genre:
        lines.append(f"🎭 {movie.genre}")
    if description:
        label = "📝 Tavsif:" if lang == "uz" else "📝 Описание:" if lang == "ru" else "📝 Description:"
        lines.append(f"\n{label}\n{description[:300]}{'...' if len(description) > 300 else ''}")
    lines.append(f"\n🔎 Kod: <code>{movie.code}</code>")

    return "\n".join(lines)


def get_video_caption(movie, lang: str = "uz", bot_username: str = "", channel_username: str = "") -> str:
    """Build caption for the video file message."""
    title = getattr(movie, f"title_{lang}", None) or movie.title_original
    description = getattr(movie, f"description_{lang}", None) or ""

    lines = [f"🎬 <b>{title}</b>"]
    if description:
        # Short description for video caption
        desc_label = "📝 Tavsif:" if lang == "uz" else "📝 Описание:" if lang == "ru" else "📝 Description:"
        lines.append(f"\n{desc_label}\n{description[:250]}{'...' if len(description) > 250 else ''}")

    lines.append(f"\n🤖 Bot: @{bot_username.strip('@')}")
    if channel_username:
        ch = channel_username.strip('@').split('/')[-1] # Handle full links
        lines.append(f"📢 Kanalimiz: @{ch}")
    
    lines.append(f"🔎 Kod: <code>{movie.code}</code>")

    return "\n".join(lines)

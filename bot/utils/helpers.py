import random
import string
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from bot.config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return user_id in settings.admin_ids_list


def generate_referral_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_movie_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def flag_for_language(lang: str) -> str:
    flags = {"uz": "🇺🇿", "ru": "🇷🇺", "en": "🇬🇧"}
    return flags.get(lang, "🌐")


def lang_label(lang: str) -> str:
    labels = {"uz": "Uzbek", "ru": "Russian", "en": "English"}
    return labels.get(lang, lang.upper())


def quality_label(quality: str) -> str:
    return quality


def dub_label(dub: str, lang: str = "uz") -> str:
    labels = {
        "uz": {
            "original": "Original",
            "professional": "Professional",
            "amateur": "Havaskor",
            "subtitle": "Subtitr",
        },
        "ru": {
            "original": "Оригинал",
            "professional": "Профессиональный",
            "amateur": "Любительский",
            "subtitle": "Субтитры",
        },
        "en": {
            "original": "Original",
            "professional": "Professional",
            "amateur": "Amateur",
            "subtitle": "Subtitle",
        },
    }
    return labels.get(lang, labels["uz"]).get(dub, dub)


def format_version_button(version, lang: str = "uz") -> str:
    prefix = "💎 " if version.is_premium else ""
    flag = flag_for_language(version.language)
    lang_name = lang_label(version.language)
    dub = dub_label(version.dub_type, lang)
    size = f" | {version.file_size}" if version.file_size else ""
    return f"{prefix}{flag} {lang_name} | {version.quality} | {dub}{size}"


def format_episode_version_button(version, lang: str = "uz") -> str:
    prefix = "💎 " if version.is_premium else ""
    flag = flag_for_language(version.language)
    lang_name = lang_label(version.language)
    return f"{prefix}{flag} {lang_name} | {version.quality}"

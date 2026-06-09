import json
import re
from typing import Optional, List, Dict
import google.generativeai as genai
from bot.config import settings
from bot.utils.logger import logger

genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def _generate(self, prompt: str) -> str:
        try:
            # Use explicit model name from settings
            model_name = settings.GEMINI_MODEL
            # If model name doesn't start with models/, it might be better to add it or let SDK handle
            # The SDK usually handles it, but let's be explicit if needed.
            
            response = self.model.generate_content(prompt)
            if not response:
                logger.error("Gemini returned empty response")
                return ""
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini error ({settings.GEMINI_MODEL}): {e}")
            # Log more details if available
            if hasattr(e, 'details'):
                logger.error(f"Gemini error details: {e.details}")
            return ""

    # ─── Movie Info ───────────────────────────────────────────────────────────

    async def get_movie_info(self, movie_name: str) -> Optional[Dict]:
        """Generate movie info JSON for admin movie creation."""
        prompt = f"""
Sen kino bazasi mutaxassisisan. Quyidagi kino haqida to'liq JSON ma'lumot ber:

Kino: "{movie_name}"

FAQAT quyidagi JSON formatda javob ber, boshqa hech narsa yozma:
{{
    "title_original": "Asl nomi",
    "title_uz": "O'zbek nomiga tarjimasi yoki transliteratsiya",
    "title_ru": "Ruscha nomiga tarjimasi",
    "title_en": "Inglizcha nomi",
    "description_uz": "O'zbek tilida 2-3 jumlali tavsif",
    "description_ru": "Ruscha 2-3 jumlali tavsif",
    "description_en": "English 2-3 sentence description",
    "short_caption_uz": "O'zbek tilida 1 jumlali qisqa tavsif",
    "short_caption_ru": "Ruscha 1 jumlali qisqa tavsif",
    "short_caption_en": "English 1 sentence caption",
    "genre": "Janrlar vergul bilan, masalan: Drama, Triller",
    "year": 2023,
    "country": "AQSh",
    "actors": "Asosiy aktyorlar vergul bilan",
    "imdb_rating": 8.5,
    "duration": 148,
    "age_limit": "16+",
    "keywords": "kalit so'zlar vergul bilan, qidiruv uchun"
}}

Faqat JSON, markdown yoki backtick ishlatma.
"""
        text = await self._generate(prompt)
        text = text.strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Gemini JSON: {text[:200]}")
            return None

    # ─── AI Recommendation ────────────────────────────────────────────────────

    async def recommend_movies(
        self,
        user_query: str,
        available_movies: List[Dict],
        lang: str = "uz",
    ) -> str:
        """Recommend movies from the DB based on user's description."""

        if not available_movies:
            no_movie = {
                "uz": "Afsuski, bazada hozircha mos kino topilmadi. Yangi kinolar tez orada qo'shiladi!",
                "ru": "К сожалению, подходящих фильмов в базе пока нет. Новые фильмы скоро будут добавлены!",
                "en": "Unfortunately, no matching movies found in the database yet. New movies will be added soon!",
            }
            return no_movie.get(lang, no_movie["uz"])

        movies_text = "\n".join([
            f"- [{m['code']}] {m['title']} ({m.get('year', '?')}) | {m.get('genre', '')} | IMDb: {m.get('imdb_rating', '?')}"
            for m in available_movies[:30]
        ])

        lang_map = {"uz": "o'zbek", "ru": "ruscha", "en": "inglizcha"}
        lang_label = lang_map.get(lang, "o'zbek")

        prompt = f"""
Sen kino tavsiya beruvchi AI assistantsan. Senda quyidagi kinolar bor:

{movies_text}

Foydalanuvchi so'rovi: "{user_query}"

Ushbu so'rovga asoslanib, ro'yxatdan ENG MOS 3-5 ta kinoni tavsiya qil.
MUHIM: Faqat ro'yxatdagi kinolarni tavsiya qil. Ro'yxatda yo'q kinolarni aytma!
Javobni {lang_label} tilida yoz.
Har bir kinoni qisqacha nima uchun mos ekanini tushuntir.
Kod bilan birga yoz: [KOD] Kino nomi - sabab
"""
        return await self._generate(prompt)

    # ─── Find Movie by Description ────────────────────────────────────────────

    async def find_movie_by_description(
        self,
        user_description: str,
        available_movies: List[Dict],
        lang: str = "uz",
    ) -> str:
        """Help user find a movie they can't name."""

        if not available_movies:
            no_movie = {
                "uz": "Bazada hozircha kino yo'q.",
                "ru": "В базе пока нет фильмов.",
                "en": "No movies in the database yet.",
            }
            return no_movie.get(lang, no_movie["uz"])

        movies_text = "\n".join([
            f"- [{m['code']}] {m['title']} ({m.get('year', '?')}) | {m.get('genre', '')}"
            for m in available_movies[:50]
        ])

        lang_map = {"uz": "o'zbek", "ru": "ruscha", "en": "inglizcha"}
        lang_label = lang_map.get(lang, "o'zbek")

        prompt = f"""
Sen kino topishda yordam beruvchi AI assistantsan. Senda quyidagi kinolar mavjud:

{movies_text}

Foydalanuvchi shu kinoni qidirmoqda: "{user_description}"

Ro'yxatdan bu tavsifga mos keladigan kinolarni top va javob ber.
MUHIM: Faqat ro'yxatdagi kinolar haqida gapirlolasan!
Agar ro'yxatda topilmasa: "Bu kino hozircha bazada yo'q" de.
Javobni {lang_label} tilida yoz.
Har bir topilgan kino: [KOD] Kino nomi - nima uchun mos
"""
        return await self._generate(prompt)

    # ─── Description Translation ──────────────────────────────────────────────

    async def translate_description(self, text: str) -> Dict[str, str]:
        """Translate movie description to 3 languages."""
        prompt = f"""
Quyidagi kino tavsifini 3 tilda tarjima qil va FAQAT JSON format bilan qaytargin:

Tavsif: "{text}"

{{
    "uz": "O'zbek tilida tarjima",
    "ru": "Ruscha tarjima",
    "en": "English translation"
}}

Faqat JSON, boshqa hech narsa yozma.
"""
        raw = await self._generate(prompt)
        raw = raw.strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"uz": text, "ru": text, "en": text}

    # ─── SEO Keywords ─────────────────────────────────────────────────────────

    async def generate_keywords(self, movie_info: Dict) -> str:
        """Generate SEO keywords for a movie."""
        prompt = f"""
Quyidagi kino uchun qidiruv kalit so'zlarini yaratib ber:
Nomi: {movie_info.get('title_original')}
Janr: {movie_info.get('genre')}
Aktyorlar: {movie_info.get('actors')}

20 ta kalit so'z ber, vergul bilan ajratilgan. Faqat kalit so'zlar, boshqa hech narsa yozma.
"""
        return await self._generate(prompt)

    # ─── Caption Generator ────────────────────────────────────────────────────

    async def generate_caption(self, movie_info: Dict, lang: str = "uz") -> str:
        """Generate short attractive caption for a movie."""
        lang_map = {"uz": "o'zbek", "ru": "ruscha", "en": "inglizcha"}
        prompt = f"""
Quyidagi kino uchun {lang_map.get(lang, 'o\'zbek')} tilida qisqa va jalb qiluvchi tavsif yoz (1-2 jumla):

Kino: {movie_info.get('title_original')}
Janr: {movie_info.get('genre')}
Yil: {movie_info.get('year')}

Faqat tavsif matni, boshqa hech narsa yozma.
"""
        return await self._generate(prompt)

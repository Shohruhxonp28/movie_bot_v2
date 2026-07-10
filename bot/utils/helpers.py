import random
import string
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from bot.config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return user_id in settings.admin_ids_list


def generate_movie_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

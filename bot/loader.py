from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import settings

# Bot instance
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# FSM Storage
storage = MemoryStorage()
if settings.REDIS_URL:
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        import redis
        # Test connection immediately
        client = redis.from_url(settings.REDIS_URL)
        client.ping()
        storage = RedisStorage.from_url(settings.REDIS_URL)
    except Exception:
        pass

dp = Dispatcher(storage=storage)

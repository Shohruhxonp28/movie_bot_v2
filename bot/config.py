from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    DATABASE_URL: str
    BOT_USERNAME: str

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Channels
    PUBLIC_CHANNEL_ID: str = ""
    PUBLIC_CHANNEL_USERNAME: str = ""
    MAIN_CHANNEL_ID: str = ""
    MAIN_CHANNEL_USERNAME: str = ""

    # Admin group for payment checks
    ADMIN_GROUP_ID: str = ""
    PAYMENT_CARD: str = ""
    PAYMENT_NAME: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Settings
    WATERMARK_TEXT: str = "@kinobot"
    DEFAULT_LANGUAGE: str = "uz"
    MAX_SEARCH_RESULTS: int = 10
    DAILY_DOWNLOAD_LIMIT: int = 5
    VIP_DAILY_LIMIT: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]


settings = Settings()

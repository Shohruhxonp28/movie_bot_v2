from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class Language(str, enum.Enum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class MovieType(str, enum.Enum):
    FILM = "film"
    SERIAL = "serial"
    ANIME = "anime"
    MULTFILM = "multfilm"


class Quality(str, enum.Enum):
    Q360 = "360p"
    Q480 = "480p"
    Q720 = "720p"
    Q1080 = "1080p"
    Q4K = "4K"


class DubType(str, enum.Enum):
    ORIGINAL = "original"
    PROFESSIONAL = "professional"
    AMATEUR = "amateur"
    SUBTITLE = "subtitle"


class TrailerType(str, enum.Enum):
    NONE = "none"
    VIDEO = "video"
    URL = "url"


class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"


# ─── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(256), default="")
    language: Mapped[str] = mapped_column(String(5), default="uz")
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    vip_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[Optional[str]] = mapped_column(String(32), unique=True)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    daily_downloads: Mapped[int] = mapped_column(Integer, default=0)
    last_download_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    pending_movie_code: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    downloads = relationship("DownloadLog", back_populates="user")
    saved_movies = relationship("SavedMovie", back_populates="user")
    referrals = relationship("User", foreign_keys=[referred_by])


# ─── Channels ─────────────────────────────────────────────────────────────────

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    channel_id: Mapped[str] = mapped_column(String(32), unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    invite_link: Mapped[Optional[str]] = mapped_column(String(256))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ─── Movies ───────────────────────────────────────────────────────────────────

class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    movie_type: Mapped[str] = mapped_column(String(20), default="film")

    title_original: Mapped[str] = mapped_column(String(256), index=True)
    title_uz: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    title_ru: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    title_en: Mapped[Optional[str]] = mapped_column(String(256), index=True)

    description_uz: Mapped[Optional[str]] = mapped_column(Text)
    description_ru: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)

    short_caption_uz: Mapped[Optional[str]] = mapped_column(Text)
    short_caption_ru: Mapped[Optional[str]] = mapped_column(Text)
    short_caption_en: Mapped[Optional[str]] = mapped_column(Text)

    genre: Mapped[Optional[str]] = mapped_column(String(256))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    country: Mapped[Optional[str]] = mapped_column(String(128))
    actors: Mapped[Optional[str]] = mapped_column(Text)
    imdb_rating: Mapped[Optional[float]] = mapped_column(Float)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    age_limit: Mapped[Optional[str]] = mapped_column(String(16))
    keywords: Mapped[Optional[str]] = mapped_column(Text)

    poster_file_id: Mapped[Optional[str]] = mapped_column(String(256))
    poster_watermarked_file_id: Mapped[Optional[str]] = mapped_column(String(256))

    trailer_type: Mapped[str] = mapped_column(String(10), default="none")
    trailer_file_id: Mapped[Optional[str]] = mapped_column(String(256))
    trailer_url: Mapped[Optional[str]] = mapped_column(String(512))

    public_post_message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    public_posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    versions = relationship("MovieVersion", back_populates="movie", cascade="all, delete-orphan")
    episodes = relationship("Episode", back_populates="movie", cascade="all, delete-orphan")


class MovieVersion(Base):
    __tablename__ = "movie_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"))
    file_id: Mapped[str] = mapped_column(String(256))
    quality: Mapped[str] = mapped_column(String(10))
    language: Mapped[str] = mapped_column(String(20))
    dub_type: Mapped[str] = mapped_column(String(20), default="professional")
    file_size: Mapped[Optional[str]] = mapped_column(String(32))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    movie = relationship("Movie", back_populates="versions")


# ─── Episodes ─────────────────────────────────────────────────────────────────

class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"))
    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    movie = relationship("Movie", back_populates="episodes")
    versions = relationship("EpisodeVersion", back_populates="episode", cascade="all, delete-orphan")


class EpisodeVersion(Base):
    __tablename__ = "episode_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"))
    file_id: Mapped[str] = mapped_column(String(256))
    quality: Mapped[str] = mapped_column(String(10))
    language: Mapped[str] = mapped_column(String(20))
    dub_type: Mapped[str] = mapped_column(String(20), default="professional")
    file_size: Mapped[Optional[str]] = mapped_column(String(32))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    episode = relationship("Episode", back_populates="versions")


# ─── VIP ──────────────────────────────────────────────────────────────────────

class VIPPlan(Base):
    __tablename__ = "vip_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_uz: Mapped[str] = mapped_column(String(128))
    name_ru: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    duration_days: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VIPSubscription(Base):
    __tablename__ = "vip_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vip_plans.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    granted_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ─── Logs ─────────────────────────────────────────────────────────────────────

class SearchLog(Base):
    __tablename__ = "search_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    query: Mapped[str] = mapped_column(String(512))
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DownloadLog(Base):
    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    movie_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("movies.id"), nullable=True)
    version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="downloads")


class SavedMovie(Base):
    __tablename__ = "saved_movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="saved_movies")
    movie = relationship("Movie")


# ─── Ads ──────────────────────────────────────────────────────────────────────

class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(256))
    media_type: Mapped[Optional[str]] = mapped_column(String(20))
    button_text: Mapped[Optional[str]] = mapped_column(String(128))
    button_url: Mapped[Optional[str]] = mapped_column(String(512))
    show_after_download: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    bonus_given: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

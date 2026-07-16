from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
    daily_downloads: Mapped[int] = mapped_column(Integer, default=0)
    last_download_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    pending_movie_code: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    downloads = relationship("DownloadLog", back_populates="user")


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
    title: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    short_caption: Mapped[Optional[str]] = mapped_column(Text)

    genre: Mapped[Optional[str]] = mapped_column(String(256))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    country: Mapped[Optional[str]] = mapped_column(String(128))
    actors: Mapped[Optional[str]] = mapped_column(Text)
    imdb_rating: Mapped[Optional[float]] = mapped_column(Float)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    age_limit: Mapped[Optional[str]] = mapped_column(String(16))
    keywords: Mapped[Optional[str]] = mapped_column(Text)

    poster_file_id: Mapped[Optional[str]] = mapped_column(String(256))
    file_id: Mapped[Optional[str]] = mapped_column(String(256))
    database_message_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    trailer_type: Mapped[str] = mapped_column(String(10), default="none")
    trailer_file_id: Mapped[Optional[str]] = mapped_column(String(256))
    trailer_url: Mapped[Optional[str]] = mapped_column(String(512))


    public_post_message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    public_posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── VIP ──────────────────────────────────────────────────────────────────────

class VIPPlan(Base):
    __tablename__ = "vip_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="downloads")


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

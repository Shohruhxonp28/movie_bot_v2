"""Initial migration with pg_trgm

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm for fuzzy search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(256), nullable=False, server_default=""),
        sa.Column("language", sa.String(5), nullable=False, server_default="uz"),
        sa.Column("is_vip", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("vip_until", sa.DateTime(), nullable=True),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("referral_code", sa.String(32), nullable=True, unique=True),
        sa.Column("referred_by", sa.BigInteger(), nullable=True),
        sa.Column("daily_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_download_date", sa.DateTime(), nullable=True),
        sa.Column("pending_movie_code", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("channel_id", sa.String(32), nullable=False, unique=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("invite_link", sa.String(256), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("movie_type", sa.String(20), nullable=False, server_default="film"),
        sa.Column("title_original", sa.String(256), nullable=False),
        sa.Column("title_uz", sa.String(256), nullable=True),
        sa.Column("title_ru", sa.String(256), nullable=True),
        sa.Column("title_en", sa.String(256), nullable=True),
        sa.Column("description_uz", sa.Text(), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("short_caption_uz", sa.Text(), nullable=True),
        sa.Column("short_caption_ru", sa.Text(), nullable=True),
        sa.Column("short_caption_en", sa.Text(), nullable=True),
        sa.Column("genre", sa.String(256), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("actors", sa.Text(), nullable=True),
        sa.Column("imdb_rating", sa.Float(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("age_limit", sa.String(16), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("poster_file_id", sa.String(256), nullable=True),
        sa.Column("poster_watermarked_file_id", sa.String(256), nullable=True),
        sa.Column("trailer_type", sa.String(10), nullable=False, server_default="none"),
        sa.Column("trailer_file_id", sa.String(256), nullable=True),
        sa.Column("trailer_url", sa.String(512), nullable=True),
        sa.Column("public_post_message_id", sa.BigInteger(), nullable=True),
        sa.Column("public_posted_at", sa.DateTime(), nullable=True),
        sa.Column("is_vip", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Trigram indexes for fuzzy search
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_title_orig_trgm ON movies USING GIN (title_original gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_title_uz_trgm ON movies USING GIN (COALESCE(title_uz, '') gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_title_ru_trgm ON movies USING GIN (COALESCE(title_ru, '') gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_movies_title_en_trgm ON movies USING GIN (COALESCE(title_en, '') gin_trgm_ops)")

    op.create_table(
        "movie_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.String(256), nullable=False),
        sa.Column("quality", sa.String(10), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("dub_type", sa.String(20), nullable=False, server_default="professional"),
        sa.Column("file_size", sa.String(32), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("downloads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "episode_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.String(256), nullable=False),
        sa.Column("quality", sa.String(10), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("dub_type", sa.String(20), nullable=False, server_default="professional"),
        sa.Column("file_size", sa.String(32), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("downloads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "vip_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_uz", sa.String(128), nullable=False),
        sa.Column("name_ru", sa.String(128), nullable=False),
        sa.Column("name_en", sa.String(128), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "vip_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("vip_plans.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("granted_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "search_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query", sa.String(512), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "download_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "saved_movies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "ads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("media_file_id", sa.String(256), nullable=True),
        sa.Column("media_type", sa.String(20), nullable=True),
        sa.Column("button_text", sa.String(128), nullable=True),
        sa.Column("button_url", sa.String(512), nullable=True),
        sa.Column("show_after_download", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("referrer_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("referred_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("bonus_given", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("referrals")
    op.drop_table("ads")
    op.drop_table("saved_movies")
    op.drop_table("download_logs")
    op.drop_table("search_logs")
    op.drop_table("vip_subscriptions")
    op.drop_table("vip_plans")
    op.drop_table("episode_versions")
    op.drop_table("episodes")
    op.drop_table("movie_versions")
    op.drop_table("movies")
    op.drop_table("channels")
    op.drop_table("users")

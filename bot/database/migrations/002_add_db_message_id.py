"""Add database_message_id to versions

Revision ID: 002
Revises: 001
Create Date: 2025-06-19 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("movie_versions", sa.Column("database_message_id", sa.BigInteger(), nullable=True))
    op.add_column("episode_versions", sa.Column("database_message_id", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("movie_versions", "database_message_id")
    op.drop_column("episode_versions", "database_message_id")

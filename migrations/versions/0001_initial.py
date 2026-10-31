"""initial tables

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("api_key_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "links",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_links_user_created",
        "links",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_table(
        "clicks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("link_id", sa.BigInteger, sa.ForeignKey("links.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referer", sa.Text(), nullable=True),
        sa.Column("device", sa.String(16), nullable=True),
        sa.Column("browser", sa.String(64), nullable=True),
        sa.Column("country", sa.CHAR(2), nullable=True),
        sa.Column("ip_hash", sa.CHAR(16), nullable=True),
    )
    op.create_index(
        "ix_clicks_link_ts",
        "clicks",
        ["link_id", sa.text("ts DESC")],
    )

def downgrade() -> None:
    op.drop_index("ix_clicks_link_ts", table_name="clicks")
    op.drop_table("clicks")
    op.drop_index("ix_links_user_created", table_name="links")
    op.drop_table("links")
    op.drop_table("users")

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code:Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    __table_args__ = (
        Index("ix_links_user_created", "user_id", text("created_at DESC")),
    )

class Click(Base):
    """becomes timescaledb hypertable on ts so ts must be part of the primarykey"""
    __tablename__ = "clicks"
    __table_args__ = (Index("ix_clicks_link_ts", "link_id", text("ts DESC")),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    link_id: Mapped[int] = mapped_column(BigInteger,ForeignKey("links.id", ondelete="CASCADE"), nullable=False)
    referer: Mapped[str | None] = mapped_column(Text)
    device: Mapped[str | None] = mapped_column(String(16))
    browser: Mapped[str | None] = mapped_column(String(64))
    country: Mapped[str | None] = mapped_column(CHAR(2))
    ip_hash: Mapped[str | None] = mapped_column(CHAR(16))
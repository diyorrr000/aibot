from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class BusinessConnectionModel(Base):
    __tablename__ = "business_connections"

    connection_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    can_reply: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rights: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BusinessSettingsModel(Base):
    __tablename__ = "business_settings"

    connection_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    model_name: Mapped[str] = mapped_column(String(64), default="gpt-4o-mini")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

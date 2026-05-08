import uuid
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    Integer, Boolean, JSON, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: "u_" + uuid.uuid4().hex[:12])
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String, default="")
    nickname = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    conversations = relationship("Conversation", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(String, primary_key=True, default=lambda: "us_" + uuid.uuid4().hex[:12])
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    theme = Column(String, default="light")
    default_model_id = Column(String, default="openrouter/auto")
    tts_speaker = Column(String, default="vv")
    extra_settings = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    user = relationship("User", back_populates="settings")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: "c_" + uuid.uuid4().hex[:12])
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    mode = Column(String, nullable=False, index=True)  # "chat" or "voice"
    model_id = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, onupdate=func.now())
    last_message_at = Column(DateTime, server_default=func.now(), index=True)
    deleted_at = Column(DateTime, nullable=True)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")

    __table_args__ = (
        Index('idx_conv_user_lastmsg', 'user_id', 'last_message_at'),
    )


class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: "m_" + uuid.uuid4().hex[:12])
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False, index=True)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    model_id = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    status = Column(String, default="completed", index=True)  # "sending", "completed", "failed"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    deleted_at = Column(DateTime, nullable=True)
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
    )

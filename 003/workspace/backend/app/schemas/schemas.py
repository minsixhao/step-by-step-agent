from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# -- Auth --
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    nickname: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str
    avatar_url: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserSettingsResponse(BaseModel):
    id: str
    theme: str
    default_model_id: str
    tts_speaker: str
    extra_settings: dict = {}

    class Config:
        from_attributes = True


class UpdateUserSettingsRequest(BaseModel):
    theme: Optional[str] = None
    default_model_id: Optional[str] = None
    tts_speaker: Optional[str] = None
    extra_settings: Optional[dict] = None


# -- Conversation --
class ConversationCreate(BaseModel):
    title: str = "New Chat"
    mode: str = "chat"  # "chat" or "voice"
    model_id: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    mode: str
    model_id: Optional[str] = None
    summary: Optional[str] = None
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: str
    title: str
    mode: str
    summary: Optional[str] = None
    is_archived: bool
    created_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None


# -- Message --
class MessageCreate(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    model_id: Optional[str] = None
    tokens_used: Optional[int] = None
    status: str = "completed"


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model_id: Optional[str] = None
    tokens_used: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int


# -- Chat Stream --
class ChatStreamRequest(BaseModel):
    conversation_id: str
    model_id: str = "openrouter/auto"
    message: str
    image_urls: Optional[List[str]] = None


# -- Search --
class SearchRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None


class SearchResult(BaseModel):
    type: str  # "conversation" or "message"
    conversation_id: Optional[str] = None
    conversation_title: Optional[str] = None
    message_id: Optional[str] = None
    content: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    highlight: Optional[str] = None


# -- Merge --
class MergeLocalRequest(BaseModel):
    conversations: List[dict]
    messages: List[dict]


class MergeResponse(BaseModel):
    merged_conversations: int
    merged_messages: int
    skipped: int


# -- Upload --
class UploadResponse(BaseModel):
    url: str
    filename: str
    size: int


# -- Model --
class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    context_length: Optional[int] = None
    pricing: Optional[dict] = None


class ModelListResponse(BaseModel):
    models: List[ModelInfo]

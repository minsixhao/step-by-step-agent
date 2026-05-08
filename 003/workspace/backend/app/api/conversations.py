from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, or_, and_, text, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.db_models import User, Conversation, Message
from app.schemas.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationListItem, MessageCreate, MessageResponse,
    MessageListResponse, SearchResult,
)

router = APIRouter(tags=["conversations"])


async def _get_user_id(request: Request, current_user: Optional[User]) -> Optional[str]:
    if current_user:
        return current_user.id
    guest_id = request.headers.get("x-guest-id")
    return guest_id if guest_id else None


# ==================== List & Create ====================

@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    request: Request,
    mode: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    if not user_id:
        return []

    conditions = [
        Conversation.user_id == user_id,
        Conversation.deleted_at.is_(None),
    ]
    if mode:
        conditions.append(Conversation.mode == mode)

    query = (
        select(Conversation)
        .where(and_(*conditions))
        .order_by(desc(Conversation.last_message_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    conversations = result.scalars().all()

    items = []
    for conv in conversations:
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id, Message.deleted_at.is_(None))
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()
        items.append(ConversationListItem(
            id=conv.id,
            title=conv.title,
            mode=conv.mode,
            summary=conv.summary,
            is_archived=conv.is_archived,
            created_at=conv.created_at,
            last_message_at=conv.last_message_at,
            last_message_preview=last_msg.content[:100] if last_msg else None,
        ))
    return items


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    req: ConversationCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication or guest ID required")

    conv = Conversation(
        user_id=user_id,
        title=req.title,
        mode=req.mode,
        model_id=req.model_id,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse(
        id=conv.id, user_id=conv.user_id, title=conv.title,
        mode=conv.mode, model_id=conv.model_id, summary=conv.summary,
        is_archived=conv.is_archived, created_at=conv.created_at,
        updated_at=conv.updated_at, last_message_at=conv.last_message_at,
    )


# ==================== Search & Merge (BEFORE /{id} routes) ====================

@router.get("/conversations/search", response_model=List[SearchResult])
async def search_conversations(
    request: Request,
    q: str = Query(..., min_length=1),
    conversation_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    if not user_id:
        return []

    results = []
    if not conversation_id:
        conv_q = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
            Conversation.title.ilike(f"%{q}%"),
        )
        conv_result = await db.execute(conv_q)
        for conv in conv_result.scalars().all():
            results.append(SearchResult(
                type="conversation", conversation_id=conv.id,
                conversation_title=conv.title, created_at=conv.created_at,
            ))

    msg_conditions = [
        Message.deleted_at.is_(None),
        Message.content.ilike(f"%{q}%"),
    ]
    if conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        if not conv_result.scalar_one_or_none():
            return []
        msg_conditions.append(Message.conversation_id == conversation_id)
    else:
        msg_conditions.append(
            Message.conversation_id.in_(
                select(Conversation.id).where(
                    Conversation.user_id == user_id,
                    Conversation.deleted_at.is_(None),
                )
            )
        )

    msg_q = (
        select(Message, Conversation.title)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(and_(*msg_conditions))
        .order_by(desc(Message.created_at))
        .limit(50)
    )
    msg_result = await db.execute(msg_q)
    for msg, conv_title in msg_result.all():
        results.append(SearchResult(
            type="message", conversation_id=msg.conversation_id,
            conversation_title=conv_title, message_id=msg.id,
            content=msg.content[:200], role=msg.role, created_at=msg.created_at,
        ))
    return results


@router.post("/conversations/merge-local")
async def merge_local(
    req: dict,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    convs = req.get("conversations", [])
    msgs = req.get("messages", [])
    merged_convs = 0
    merged_msgs = 0
    skipped = 0
    conv_id_map = {}

    for conv_data in convs:
        new_conv = Conversation(
            user_id=current_user.id,
            title=conv_data.get("title", "Imported Chat"),
            mode=conv_data.get("mode", "chat"),
            model_id=conv_data.get("model_id"),
            created_at=conv_data.get("created_at"),
        )
        db.add(new_conv)
        await db.flush()
        conv_id_map[conv_data.get("id")] = new_conv.id
        merged_convs += 1

    for msg_data in msgs:
        new_cid = conv_id_map.get(msg_data.get("conversation_id"))
        if not new_cid:
            skipped += 1
            continue
        existing = await db.execute(
            select(Message).where(
                Message.conversation_id == new_cid,
                Message.content == msg_data.get("content", ""),
                Message.role == msg_data.get("role", "user"),
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        new_msg = Message(
            conversation_id=new_cid,
            role=msg_data.get("role", "user"),
            content=msg_data.get("content", ""),
            model_id=msg_data.get("model_id"),
            status=msg_data.get("status", "completed"),
            created_at=msg_data.get("created_at"),
        )
        db.add(new_msg)
        merged_msgs += 1

    await db.commit()
    return {"merged_conversations": merged_convs, "merged_messages": merged_msgs, "skipped": skipped}


# ==================== Single Conversation CRUD ====================

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None),
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user_id and conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return ConversationResponse(
        id=conv.id, user_id=conv.user_id, title=conv.title,
        mode=conv.mode, model_id=conv.model_id, summary=conv.summary,
        is_archived=conv.is_archived, created_at=conv.created_at,
        updated_at=conv.updated_at, last_message_at=conv.last_message_at,
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    req: ConversationUpdate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None),
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user_id and conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if req.title is not None:
        conv.title = req.title
    if req.is_archived is not None:
        conv.is_archived = req.is_archived

    await db.commit()
    await db.refresh(conv)
    return ConversationResponse(
        id=conv.id, user_id=conv.user_id, title=conv.title,
        mode=conv.mode, model_id=conv.model_id, summary=conv.summary,
        is_archived=conv.is_archived, created_at=conv.created_at,
        updated_at=conv.updated_at, last_message_at=conv.last_message_at,
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None),
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user_id and conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    conv.deleted_at = now
    await db.execute(
        text("UPDATE messages SET deleted_at = :now WHERE conversation_id = :cid AND deleted_at IS NULL"),
        {"now": now, "cid": conversation_id}
    )
    await db.commit()
    return {"message": "Conversation deleted"}


# ==================== Messages ====================

@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def list_messages(
    conversation_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None),
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user_id and conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    count_q = select(func.count(Message.id)).where(
        Message.conversation_id == conversation_id,
        Message.deleted_at.is_(None),
    )
    total = (await db.execute(count_q)).scalar() or 0

    msg_q = (
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
        .order_by(Message.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    msg_result = await db.execute(msg_q)
    messages = msg_result.scalars().all()

    return MessageListResponse(
        messages=[MessageResponse(
            id=m.id, conversation_id=m.conversation_id, role=m.role,
            content=m.content, model_id=m.model_id, tokens_used=m.tokens_used,
            status=m.status, error_message=m.error_message, created_at=m.created_at,
        ) for m in messages],
        total=total, page=page, page_size=page_size,
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def save_message(
    conversation_id: str,
    req: MessageCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.deleted_at.is_(None),
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user_id and conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    msg = Message(
        conversation_id=conversation_id, role=req.role,
        content=req.content, model_id=req.model_id,
        tokens_used=req.tokens_used, status=req.status,
    )
    db.add(msg)

    if req.role == "user":
        count_q = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.role == "user",
            Message.deleted_at.is_(None),
        )
        existing_count = (await db.execute(count_q)).scalar() or 0
        if existing_count == 0 and conv.title in ("New Chat", "New Voice Chat"):
            conv.title = req.content[:30] + ("..." if len(req.content) > 30 else "")

    conv.last_message_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(msg)
    return MessageResponse(
        id=msg.id, conversation_id=msg.conversation_id, role=msg.role,
        content=msg.content, model_id=msg.model_id, tokens_used=msg.tokens_used,
        status=msg.status, error_message=msg.error_message, created_at=msg.created_at,
    )


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await _get_user_id(request, current_user)
    result = await db.execute(
        select(Message).join(Conversation).where(
            Message.id == message_id,
            Message.deleted_at.is_(None),
        )
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if user_id and msg.conversation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    msg.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    return {"message": "Message deleted"}

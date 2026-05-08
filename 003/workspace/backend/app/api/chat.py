import json
import asyncio
from typing import Optional, List, AsyncGenerator
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.db_models import User, Conversation
from app.schemas.schemas import ChatStreamRequest, ModelInfo, ModelListResponse

router = APIRouter(tags=["chat"])

# Model cache
_model_cache = None
_model_cache_time = 0
_CACHE_TTL = 3600  # 1 hour


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    global _model_cache, _model_cache_time
    import time
    now = time.time()

    if _model_cache and (now - _model_cache_time) < _CACHE_TTL:
        return _model_cache

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{settings.OPENROUTER_BASE_URL}/models",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:5173",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for m in data.get("data", []):
                    models.append(ModelInfo(
                        id=m.get("id", ""),
                        name=m.get("name", m.get("id", "")),
                        provider=m.get("id", "").split("/")[0] if "/" in m.get("id", "") else "",
                        context_length=m.get("context_length"),
                        pricing=m.get("pricing"),
                    ))
                _model_cache = ModelListResponse(models=models)
                _model_cache_time = now
                return _model_cache

        # Return fallback if API fails
        return ModelListResponse(models=[
            ModelInfo(id="openrouter/auto", name="Auto (best model)", provider="openrouter"),
            ModelInfo(id="openai/gpt-4o", name="GPT-4o", provider="openai"),
            ModelInfo(id="openai/gpt-4o-mini", name="GPT-4o Mini", provider="openai"),
            ModelInfo(id="anthropic/claude-3.5-sonnet", name="Claude 3.5 Sonnet", provider="anthropic"),
            ModelInfo(id="google/gemini-pro-1.5", name="Gemini Pro 1.5", provider="google"),
            ModelInfo(id="meta-llama/llama-3.1-70b", name="Llama 3.1 70B", provider="meta"),
        ])
    except Exception:
        return ModelListResponse(models=[
            ModelInfo(id="openrouter/auto", name="Auto (best model)", provider="openrouter"),
            ModelInfo(id="openai/gpt-4o", name="GPT-4o", provider="openai"),
            ModelInfo(id="anthropic/claude-3.5-sonnet", name="Claude 3.5 Sonnet", provider="anthropic"),
        ])


@router.post("/chat/stream")
async def chat_stream(
    req: ChatStreamRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify conversation exists if provided
    if req.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == req.conversation_id,
                Conversation.deleted_at.is_(None),
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    async def generate():
        try:
            messages = [{"role": "user", "content": req.message}]

            # If image URLs provided, format them
            if req.image_urls:
                content_parts = [{"type": "text", "text": req.message}]
                for img_url in req.image_urls:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": img_url},
                    })
                messages = [{"role": "user", "content": content_parts}]

            payload = {
                "model": req.model_id,
                "messages": messages,
                "stream": True,
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": str(request.base_url),
                    },
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"data: {json.dumps({'error': f'OpenRouter error: {error_text.decode()[:200]}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    async for line in response.aiter_lines():
                        # Check if client disconnected
                        if await request.is_disconnected():
                            break

                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue

        except asyncio.CancelledError:
            # Stream was interrupted
            yield f"data: {json.dumps({'interrupted': True})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

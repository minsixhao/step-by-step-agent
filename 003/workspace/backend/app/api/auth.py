from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token,
    set_auth_cookie, clear_auth_cookie, get_current_user, require_user,
    get_or_create_settings
)
from app.models.db_models import User, UserSettings
from app.schemas.schemas import (
    RegisterRequest, LoginRequest, UserResponse,
    UpdateUserRequest, UserSettingsResponse, UpdateUserSettingsRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    # Check if username exists
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    # Create user
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.nickname or req.username,
    )
    db.add(user)
    await db.flush()

    # Create default settings
    await get_or_create_settings(db, user.id)
    await db.commit()

    # Set auth cookie
    token = create_access_token(user.id)
    set_auth_cookie(response, token)

    return UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == req.username, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.id)
    set_auth_cookie(response, token)

    return UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(require_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_me(
    req: UpdateUserRequest,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    if req.nickname is not None:
        current_user.nickname = req.nickname
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url
    await db.commit()
    await db.refresh(current_user)
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
    )


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    settings_obj = await get_or_create_settings(db, current_user.id)
    return UserSettingsResponse(
        id=settings_obj.id,
        theme=settings_obj.theme,
        default_model_id=settings_obj.default_model_id,
        tts_speaker=settings_obj.tts_speaker,
        extra_settings=settings_obj.extra_settings or {},
    )


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_settings(
    req: UpdateUserSettingsRequest,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    settings_obj = await get_or_create_settings(db, current_user.id)
    if req.theme is not None:
        settings_obj.theme = req.theme
    if req.default_model_id is not None:
        settings_obj.default_model_id = req.default_model_id
    if req.tts_speaker is not None:
        settings_obj.tts_speaker = req.tts_speaker
    if req.extra_settings is not None:
        settings_obj.extra_settings = req.extra_settings
    await db.commit()
    await db.refresh(settings_obj)
    return UserSettingsResponse(
        id=settings_obj.id,
        theme=settings_obj.theme,
        default_model_id=settings_obj.default_model_id,
        tts_speaker=settings_obj.tts_speaker,
        extra_settings=settings_obj.extra_settings or {},
    )

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .models import AuthResponse, Credentials, ProfileResponse
from .service import (
    DuplicateUsernameError,
    authenticate_user,
    load_profile,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(credentials: Credentials) -> AuthResponse:
    try:
        result = await register_user(credentials.username, credentials.password)
    except DuplicateUsernameError as exc:
        raise HTTPException(status_code=409, detail="??????") from exc

    return AuthResponse(message="????", username=result.username)


@router.post("/login", response_model=AuthResponse)
async def login(credentials: Credentials) -> AuthResponse:
    result = await authenticate_user(credentials.username, credentials.password)
    if not result:
        raise HTTPException(status_code=401, detail="????????")

    return AuthResponse(message="????", username=result.username)


@router.get("/profile", response_model=ProfileResponse)
async def profile(username: str) -> ProfileResponse:
    result = await load_profile(username)
    if not result:
        raise HTTPException(status_code=404, detail="?????")

    return ProfileResponse(username=result.username, created_at=result.created_at)

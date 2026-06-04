from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Credentials(BaseModel):
    """User supplied username/password pair."""

    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)


class AuthResponse(BaseModel):
    """Simple response returned by login/register endpoints."""

    message: str
    username: str
    access_token: str
    token_type: str = "bearer"


class ProfileResponse(BaseModel):
    """User profile details returned after authentication."""

    username: str
    created_at: datetime

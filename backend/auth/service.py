from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from psycopg import errors

from . import db


class DuplicateUsernameError(Exception):
    """Raised when attempting to create a user with an existing username."""


@dataclass(slots=True)
class AuthResult:
    username: str
    created_at: Optional[datetime] = None


def _hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


async def register_user(username: str, password: str) -> AuthResult:
    try:
        record = await db.create_user(username, _hash_password(password))
    except errors.UniqueViolation as exc:
        raise DuplicateUsernameError(str(exc)) from exc

    return AuthResult(username=record.get("username", username), created_at=record.get("created_at"))


async def authenticate_user(username: str, password: str) -> Optional[AuthResult]:
    user = await db.fetch_user(username)
    if not user:
        return None

    if user.get("password_hash") != _hash_password(password):
        return None

    return AuthResult(username=user["username"], created_at=user.get("created_at"))


async def load_profile(username: str) -> Optional[AuthResult]:
    user = await db.fetch_user(username)
    if not user:
        return None
    return AuthResult(username=user["username"], created_at=user.get("created_at"))

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_TOKEN_SECRET = os.getenv("AUTH_TOKEN_SECRET", "dev-secret-change-me")
_TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", str(7 * 24 * 60 * 60)))


class TokenError(Exception):
    """Raised when an auth token is missing, malformed, expired, or invalid."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str) -> str:
    digest = hmac.new(
        _TOKEN_SECRET.encode("utf-8"),
        message.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def create_access_token(username: str) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + _TOKEN_TTL_SECONDS,
    }
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}"
    return f"{signing_input}.{_sign(signing_input)}"


def verify_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
    except ValueError as exc:
        raise TokenError("Malformed token") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenError("Invalid token signature")

    try:
        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
    except (json.JSONDecodeError, ValueError) as exc:
        raise TokenError("Invalid token payload") from exc

    if header.get("alg") != "HS256":
        raise TokenError("Unsupported token algorithm")

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise TokenError("Token expired")

    username = payload.get("sub")
    if not isinstance(username, str) or not username:
        raise TokenError("Token missing subject")

    return payload

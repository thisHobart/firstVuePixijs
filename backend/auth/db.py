from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from dotenv import load_dotenv
from psycopg import AsyncConnection, errors
from psycopg.rows import dict_row

_BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BASE_DIR / ".env")
load_dotenv()


def _build_dsn() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    parts = [f"host={host}", f"port={port}", f"dbname={name}"]
    if user:
        parts.append(f"user={user}")
    if password:
        parts.append(f"password={password}")
    return " ".join(parts)


_DSN = _build_dsn()

_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_schema_ready = False
_schema_lock = asyncio.Lock()


async def _ensure_schema() -> None:
    global _schema_ready
    if _schema_ready:
        return

    async with _schema_lock:
        if _schema_ready:
            return

        conn = await AsyncConnection.connect(_DSN, autocommit=True)
        try:
            async with conn.cursor() as cur:
                await cur.execute(_CREATE_USERS_TABLE)
        finally:
            await conn.close()
        _schema_ready = True


@asynccontextmanager
async def get_connection() -> AsyncIterator[AsyncConnection]:
    conn = await AsyncConnection.connect(_DSN, autocommit=False, row_factory=dict_row)
    try:
        yield conn
    finally:
        await conn.close()


async def create_user(username: str, password_hash: str) -> dict:
    await _ensure_schema()
    async with get_connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                    RETURNING id, username, created_at
                    """,
                    (username, password_hash),
                )
                row = await cur.fetchone()
            await conn.commit()
            return row or {}
        except errors.UniqueViolation as exc:
            await conn.rollback()
            raise


async def fetch_user(username: str) -> Optional[dict]:
    if not username:
        return None

    await _ensure_schema()
    async with get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, username, password_hash, created_at
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,),
            )
            row = await cur.fetchone()
        await conn.rollback()
        return row

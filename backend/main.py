"""FastAPI application exposing dialogue and authentication APIs."""
from __future__ import annotations

import json as _json
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from agent import generate_dialogue
from auth.schemas import AuthResponse, Credentials, ProfileResponse
from auth.service import (
    AuthResult,
    DuplicateUsernameError,
    authenticate_user,
    load_profile,
    register_user,
)
from auth.tokens import TokenError, create_access_token, verify_access_token

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app = FastAPI(title="Interactive Fiction Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthResult:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )

    try:
        payload = verify_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
        ) from exc

    user = await load_profile(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    return user


class Message(BaseModel):
    """单条对话消息."""

    role: str
    content: str


class DialogueRequest(BaseModel):
    """前端发送的对话请求，包含角色和完整历史."""

    character: str
    history: List[Message] = Field(..., min_items=1, description="完整的对话历史")
    storyContext: Dict[str, Any] | None = Field(
        default=None,
        description="当前剧情上下文，用于约束 Agent 的 nextNode 建议",
    )


@app.post("/api/dialogue", response_model=List[Dict[str, Any]])
async def dialogue(
    request: DialogueRequest,
    current_user: AuthResult = Depends(get_current_user),
):
    """根据已有对话历史生成下一轮剧情."""

    print(f"Authenticated user: {current_user.username}")
    print(f"Received request for character: {request.character}")
    print(f"Conversation history: {request.history}")
    print(f"Story context: {request.storyContext}")

    conversation_history_dict = [msg.model_dump() for msg in request.history]

    try:
        response = await generate_dialogue(
            request.character,
            conversation_history_dict,
            request.storyContext,
        )
    except Exception as exc:  # 捕获生成对话的异常，返回统一错误
        print("dialogue error:", repr(exc))
        raise HTTPException(status_code=500, detail=f"dialogue failed: {exc}") from exc

    try:
        print("Response to frontend:", _json.dumps(response, ensure_ascii=False))
    except Exception:
        pass

    return response


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(credentials: Credentials) -> AuthResponse:
    """注册新用户."""

    try:
        result = await register_user(credentials.username, credentials.password)
    except DuplicateUsernameError as exc:
        raise HTTPException(status_code=409, detail="用户名已存在") from exc

    return AuthResponse(
        message="注册成功",
        username=result.username,
        access_token=create_access_token(result.username),
    )


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(credentials: Credentials) -> AuthResponse:
    """校验用户名密码并返回登录结果."""

    result = await authenticate_user(credentials.username, credentials.password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return AuthResponse(
        message="登录成功",
        username=result.username,
        access_token=create_access_token(result.username),
    )


@app.get("/api/auth/profile", response_model=ProfileResponse)
async def profile(current_user: AuthResult = Depends(get_current_user)) -> ProfileResponse:
    """查询用户档案信息."""

    return ProfileResponse(username=current_user.username, created_at=current_user.created_at)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

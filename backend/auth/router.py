from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .schemas import AuthResponse, Credentials, ProfileResponse
from .service import (
    AuthResult,
    DuplicateUsernameError,
    authenticate_user,
    load_profile,
    register_user,
)
from .tokens import (
    TokenError,
    create_access_token,
    mask_token,
    token_fingerprint,
    verify_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
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
    print(
        "Authenticated token:",
        f"user={user.username}",
        f"token={mask_token(credentials.credentials)}",
        f"fingerprint={token_fingerprint(credentials.credentials)}",
    )
    return user


@router.post("/register", response_model=AuthResponse)
async def register(credentials: Credentials) -> AuthResponse:
    try:
        result = await register_user(credentials.username, credentials.password)
    except DuplicateUsernameError as exc:
        raise HTTPException(status_code=409, detail="用户名已经存在，请换一个用户名") from exc

    return AuthResponse(
        message="注册成功",
        username=result.username,
        access_token=create_access_token(result.username),
    )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: Credentials) -> AuthResponse:
    result = await authenticate_user(credentials.username, credentials.password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return AuthResponse(
        message="登录成功",
        username=result.username,
        access_token=create_access_token(result.username),
    )


@router.get("/profile", response_model=ProfileResponse)
async def profile(current_user: AuthResult = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(username=current_user.username, created_at=current_user.created_at)

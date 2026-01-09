"""Authentication router endpoints."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.rate_limit import get_rate_limiter
from app.core.security import decode_token
from app.db.session import get_db
from app.modules.auth.repo import AuthRepository
from app.modules.auth.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.modules.auth.service import AuthService
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
limiter = get_rate_limiter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service."""
    repo = AuthRepository(db)
    return AuthService(repo)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Dependency to get current user ID from token."""
    token = credentials.credentials
    payload = decode_token(token, token_type="access")
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    return int(payload.get("sub"))


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)
@limiter.limit("5/minute")  # Stricter limit for registration
async def register(
    request: Request,
    data: UserRegister,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Register a new user.

    Returns:
        User data and tokens
    """
    user_data, tokens = service.register(email=data.email, password=data.password)
    return {"user": user_data, **tokens}


@router.post("/login", response_model=dict)
@limiter.limit("10/minute")  # Stricter limit for login
async def login(
    request: Request,
    data: UserLogin,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Authenticate user and return tokens.

    Returns:
        User data and tokens
    """
    user_data, tokens = service.login(email=data.email, password=data.password)
    return {"user": user_data, **tokens}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Returns:
        New tokens
    """
    tokens = service.refresh_token(data.refresh_token)
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Get current user information.

    Returns:
        Current user data
    """
    user_data = service.get_current_user(user_id)
    return UserResponse(**user_data)

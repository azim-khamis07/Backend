"""Authentication service for business logic."""

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.repo import AuthRepository

settings = get_settings()
logger = get_logger(__name__)


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, repo: AuthRepository) -> None:
        """Initialize service with repository."""
        self.repo = repo

    def register(self, email: str, password: str) -> tuple[dict, dict]:
        """
        Register a new user.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (user_data, tokens)

        Raises:
            ConflictError: If user already exists
        """
        # Check if user already exists
        existing_user = self.repo.get_user_by_email(email)
        if existing_user:
            raise ConflictError(f"User with email {email} already exists")

        # Hash password
        password_hash = get_password_hash(password)

        # Create user
        user = self.repo.create_user(email=email, password_hash=password_hash)

        logger.info("User registered", extra={"user_id": user.id, "email": user.email})

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        tokens = self._create_tokens(token_data)

        user_data = {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }

        return user_data, tokens

    def login(self, email: str, password: str) -> tuple[dict, dict]:
        """
        Authenticate user and return tokens.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (user_data, tokens)

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Get user
        user = self.repo.get_user_by_email(email)
        if not user:
            logger.warning("Login attempt with non-existent email", extra={"email": email})
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            logger.warning(
                "Login attempt for inactive user", extra={"user_id": user.id, "email": email}
            )
            raise AuthenticationError("User account is inactive")

        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(
                "Login attempt with invalid password", extra={"user_id": user.id, "email": email}
            )
            raise AuthenticationError("Invalid email or password")

        logger.info("User logged in", extra={"user_id": user.id, "email": user.email})

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        tokens = self._create_tokens(token_data)

        user_data = {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }

        return user_data, tokens

    def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New tokens

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_token(refresh_token, token_type="refresh")
        if not payload:
            raise AuthenticationError("Invalid refresh token")

        user_id = int(payload.get("sub"))
        user = self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid refresh token")

        # Create new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        tokens = self._create_tokens(token_data)

        logger.info("Token refreshed", extra={"user_id": user.id})

        return tokens

    def get_current_user(self, user_id: int) -> dict:
        """
        Get current user data.

        Args:
            user_id: User ID

        Returns:
            User data

        Raises:
            NotFoundError: If user not found
        """
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User")

        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }

    def _create_tokens(self, token_data: dict) -> dict:
        """Create access and refresh tokens."""
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

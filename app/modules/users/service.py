"""User service for business logic."""

from typing import Optional

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.security import get_password_hash, verify_password
from app.modules.users.repo import UserRepository

logger = get_logger(__name__)


class UserService:
    """Service for user business logic."""

    def __init__(self, repo: UserRepository) -> None:
        """Initialize service with repository."""
        self.repo = repo

    def get_user(self, user_id: int) -> dict:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User data

        Raises:
            NotFoundError: If user not found
        """
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User")

        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    def update_profile(self, user_id: int, email: Optional[str] = None) -> dict:
        """
        Update user profile.

        Args:
            user_id: User ID
            email: New email (optional)

        Returns:
            Updated user data

        Raises:
            NotFoundError: If user not found
            ConflictError: If email already exists
        """
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User")

        # Check email if provided
        if email:
            email_lower = email.lower()
            # Check if email is different
            if email_lower != user.email:
                # Check if email already exists
                existing_user = self.repo.get_by_email(email_lower)
                if existing_user and existing_user.id != user_id:
                    raise ConflictError(f"Email {email} is already in use")

                # Update email
                user.email = email_lower

        # Save changes
        user = self.repo.update(user)

        logger.info(
            "User profile updated", extra={"user_id": user_id, "email_updated": bool(email)}
        )

        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> dict:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Success message

        Raises:
            NotFoundError: If user not found
            ValidationError: If current password is incorrect
        """
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            logger.warning(
                "Password change failed - incorrect current password", extra={"user_id": user_id}
            )
            raise ValidationError("Current password is incorrect")

        # Hash new password
        new_password_hash = get_password_hash(new_password)

        # Update password
        self.repo.update_password(user_id, new_password_hash)

        logger.info("User password changed", extra={"user_id": user_id})

        return {"message": "Password changed successfully"}

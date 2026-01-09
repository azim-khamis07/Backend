"""User repository for database operations."""

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalar(stmt)

    def update(self, user: User) -> User:
        """Update user."""
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_email(self, user_id: int, new_email: str) -> Optional[User]:
        """Update user email."""
        stmt = (
            update(User).where(User.id == user_id).values(email=new_email.lower()).returning(User)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.scalar_one_or_none()

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password."""
        stmt = update(User).where(User.id == user_id).values(password_hash=password_hash)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

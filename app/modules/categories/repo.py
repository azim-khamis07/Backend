"""Category repository for database operations."""

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    """Repository for category-related database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, category_id: int, user_id: int) -> Optional[Category]:
        """Get category by ID (user-scoped)."""
        stmt = select(Category).where(and_(Category.id == category_id, Category.user_id == user_id))
        return self.db.scalar(stmt)

    def get_all_by_user(
        self,
        user_id: int,
        type_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Category], int]:
        """Get all categories for a user with optional filtering."""
        stmt = select(Category).where(Category.user_id == user_id)

        if type_filter:
            stmt = stmt.where(Category.type == type_filter.lower())

        # Get total count
        count_stmt = select(Category).where(Category.user_id == user_id)
        if type_filter:
            count_stmt = count_stmt.where(Category.type == type_filter.lower())
        total = len(list(self.db.scalars(count_stmt)))

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Category.created_at.desc())

        categories = list(self.db.scalars(stmt).all())
        return categories, total

    def get_by_name(
        self, user_id: int, name: str, category_id: Optional[int] = None
    ) -> Optional[Category]:
        """Get category by name (for duplicate checking)."""
        stmt = select(Category).where(
            and_(Category.user_id == user_id, Category.name == name.strip())
        )
        if category_id:
            stmt = stmt.where(Category.id != category_id)
        return self.db.scalar(stmt)

    def create(
        self,
        user_id: int,
        name: str,
        type: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Category:
        """Create a new category."""
        category = Category(
            user_id=user_id,
            name=name.strip(),
            type=type.lower(),
            description=description,
            color=color,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category) -> Category:
        """Update category."""
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> bool:
        """Delete category."""
        self.db.delete(category)
        self.db.commit()
        return True

"""Category service for business logic."""

from typing import Optional

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.modules.categories.repo import CategoryRepository

logger = get_logger(__name__)


class CategoryService:
    """Service for category business logic."""

    def __init__(self, repo: CategoryRepository) -> None:
        """Initialize service with repository."""
        self.repo = repo

    def get_category(self, category_id: int, user_id: int) -> dict:
        """
        Get category by ID.

        Args:
            category_id: Category ID
            user_id: User ID (for authorization)

        Returns:
            Category data

        Raises:
            NotFoundError: If category not found
        """
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise NotFoundError("Category")

        return {
            "id": category.id,
            "user_id": category.user_id,
            "name": category.name,
            "type": category.type,
            "description": category.description,
            "color": category.color,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
        }

    def list_categories(
        self,
        user_id: int,
        type_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """
        List categories for a user.

        Args:
            user_id: User ID
            type_filter: Optional filter by type (expense/income)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of categories with total count
        """
        categories, total = self.repo.get_all_by_user(
            user_id=user_id,
            type_filter=type_filter,
            skip=skip,
            limit=limit,
        )

        items = [
            {
                "id": cat.id,
                "user_id": cat.user_id,
                "name": cat.name,
                "type": cat.type,
                "description": cat.description,
                "color": cat.color,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
            }
            for cat in categories
        ]

        return {"items": items, "total": total}

    def create_category(
        self,
        user_id: int,
        name: str,
        type: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> dict:
        """
        Create a new category.

        Args:
            user_id: User ID
            name: Category name
            type: Category type (expense/income)
            description: Optional description
            color: Optional hex color code

        Returns:
            Created category data

        Raises:
            ValidationError: If category type is invalid
            ConflictError: If category name already exists for user
        """
        # Validate type
        if type.lower() not in ("expense", "income"):
            raise ValidationError("Category type must be 'expense' or 'income'")

        # Check for duplicate name
        existing = self.repo.get_by_name(user_id, name)
        if existing:
            raise ConflictError(f"Category with name '{name}' already exists")

        # Create category
        category = self.repo.create(
            user_id=user_id,
            name=name,
            type=type.lower(),
            description=description,
            color=color,
        )

        logger.info(
            "Category created",
            extra={"category_id": category.id, "user_id": user_id, "category_name": name},
        )

        return {
            "id": category.id,
            "user_id": category.user_id,
            "name": category.name,
            "type": category.type,
            "description": category.description,
            "color": category.color,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
        }

    def update_category(
        self,
        category_id: int,
        user_id: int,
        name: Optional[str] = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> dict:
        """
        Update category.

        Args:
            category_id: Category ID
            user_id: User ID (for authorization)
            name: New name (optional)
            type: New type (optional)
            description: New description (optional)
            color: New color (optional)

        Returns:
            Updated category data

        Raises:
            NotFoundError: If category not found
            ValidationError: If category type is invalid
            ConflictError: If category name already exists
        """
        # Get category
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise NotFoundError("Category")

        # Validate and update name
        if name is not None:
            name = name.strip()
            # Check for duplicate name (excluding current category)
            existing = self.repo.get_by_name(user_id, name, category_id)
            if existing:
                raise ConflictError(f"Category with name '{name}' already exists")
            category.name = name

        # Validate and update type
        if type is not None:
            type_lower = type.lower()
            if type_lower not in ("expense", "income"):
                raise ValidationError("Category type must be 'expense' or 'income'")
            category.type = type_lower

        # Update optional fields
        if description is not None:
            category.description = description
        if color is not None:
            category.color = color

        # Save changes
        category = self.repo.update(category)

        logger.info("Category updated", extra={"category_id": category_id, "user_id": user_id})

        return {
            "id": category.id,
            "user_id": category.user_id,
            "name": category.name,
            "type": category.type,
            "description": category.description,
            "color": category.color,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
        }

    def delete_category(self, category_id: int, user_id: int) -> dict:
        """
        Delete category.

        Args:
            category_id: Category ID
            user_id: User ID (for authorization)

        Returns:
            Success message

        Raises:
            NotFoundError: If category not found
        """
        # Get category
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise NotFoundError("Category")

        # Delete category
        self.repo.delete(category)

        logger.info("Category deleted", extra={"category_id": category_id, "user_id": user_id})

        return {"message": "Category deleted successfully"}

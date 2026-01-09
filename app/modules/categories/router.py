"""Category router endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.router import get_current_user_id
from app.modules.categories.repo import CategoryRepository
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from app.modules.categories.service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Dependency to get category service."""
    repo = CategoryRepository(db)
    return CategoryService(repo)


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    type_filter: Optional[str] = Query(
        None, pattern="^(expense|income)$", description="Filter by type"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> CategoryListResponse:
    """
    List all categories for the current user.

    Query Parameters:
        type_filter: Optional filter by type (expense/income)
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of categories with total count
    """
    result = service.list_categories(
        user_id=user_id,
        type_filter=type_filter,
        skip=skip,
        limit=limit,
    )
    return CategoryListResponse(**result)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    user_id: int = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Get category by ID.

    Returns:
        Category data
    """
    category_data = service.get_category(category_id, user_id)
    return CategoryResponse(**category_data)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    user_id: int = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Create a new category.

    Returns:
        Created category data
    """
    category_data = service.create_category(
        user_id=user_id,
        name=data.name,
        type=data.type,
        description=data.description,
        color=data.color,
    )
    return CategoryResponse(**category_data)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    user_id: int = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Update category.

    Returns:
        Updated category data
    """
    category_data = service.update_category(
        category_id=category_id,
        user_id=user_id,
        name=data.name,
        type=data.type,
        description=data.description,
        color=data.color,
    )
    return CategoryResponse(**category_data)


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    user_id: int = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
) -> dict:
    """
    Delete category.

    Returns:
        Success message
    """
    result = service.delete_category(category_id, user_id)
    return result

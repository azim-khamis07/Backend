"""Transaction router endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.router import get_current_user_id
from app.modules.transactions.repo import TransactionRepository
from app.modules.transactions.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.modules.transactions.service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    """Dependency to get transaction service."""
    repo = TransactionRepository(db)
    return TransactionService(repo)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    type: Optional[str] = Query(None, pattern="^(expense|income)$", description="Filter by type"),
    min_amount: Optional[Decimal] = Query(None, ge=0, description="Minimum amount filter"),
    max_amount: Optional[Decimal] = Query(None, ge=0, description="Maximum amount filter"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionListResponse:
    """
    List all transactions for the current user with filtering and pagination.

    Query Parameters:
        start_date: Optional start date filter
        end_date: Optional end date filter
        category_id: Optional category filter
        type: Optional type filter (expense/income)
        min_amount: Optional minimum amount filter
        max_amount: Optional maximum amount filter
        cursor: Optional cursor for pagination
        limit: Maximum number of records to return (1-100)

    Returns:
        Paginated list of transactions with metadata
    """
    result = service.list_transactions(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        type_filter=type,
        min_amount=min_amount,
        max_amount=max_amount,
        cursor=cursor,
        limit=limit,
    )
    return TransactionListResponse(**result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """
    Get transaction by ID.

    Returns:
        Transaction data
    """
    transaction_data = service.get_transaction(transaction_id, user_id)
    return TransactionResponse(**transaction_data)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionResponse)
async def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """
    Create a new transaction.

    Returns:
        Created transaction data
    """
    transaction_data = service.create_transaction(
        db=db,
        user_id=user_id,
        amount=data.amount,
        type=data.type,
        occurred_at=data.occurred_at,
        category_id=data.category_id,
        note=data.note,
        tags=data.tags,
    )
    return TransactionResponse(**transaction_data)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """
    Update transaction.

    Returns:
        Updated transaction data
    """
    transaction_data = service.update_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=user_id,
        amount=data.amount,
        type=data.type,
        category_id=data.category_id,
        occurred_at=data.occurred_at,
        note=data.note,
        tags=data.tags,
    )
    return TransactionResponse(**transaction_data)


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> dict:
    """
    Delete transaction.

    Returns:
        Success message
    """
    result = service.delete_transaction(db, transaction_id, user_id)
    return result

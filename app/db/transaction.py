"""Database transaction management utilities."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for database transactions.

    Automatically commits on success, rolls back on exception.

    Usage:
        with transaction(db) as session:
            # Perform database operations
            session.add(obj)
            # Transaction commits automatically on exit

    Args:
        db: Database session

    Yields:
        Session: Database session (same as input)

    Raises:
        Exception: Any exception raised within the context will trigger rollback
    """
    try:
        yield db
        db.commit()
        logger.debug("Transaction committed successfully")
    except Exception as e:
        db.rollback()
        logger.error(
            "Transaction rolled back due to error",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise

"""Tests for database transaction utilities."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.transaction import transaction


def test_transaction_commit_on_success(db_session):
    """Test transaction commits on successful operation."""
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        email="test_commit@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
    )

    with transaction(db_session):
        db_session.add(user)

    # Verify user was committed (can query it)
    db_session.refresh(user)
    assert user.id is not None
    assert user.email == "test_commit@example.com"


def test_transaction_rollback_on_exception(db_session):
    """Test transaction rolls back on exception."""
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        email="test_rollback@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
    )

    # First, create a user
    db_session.add(user)
    db_session.commit()

    # Try to create duplicate user (should raise IntegrityError)
    duplicate_user = User(
        email="test_rollback@example.com",  # Same email
        password_hash=get_password_hash("password123"),
        is_active=True,
    )

    with pytest.raises(IntegrityError):
        with transaction(db_session):
            db_session.add(duplicate_user)
            # This should trigger an exception

    # Verify duplicate user was not committed
    users = db_session.query(User).filter(User.email == "test_rollback@example.com").all()
    assert len(users) == 1  # Only the original user


def test_transaction_raises_exception(db_session):
    """Test transaction re-raises exception after rollback."""
    with pytest.raises(ValueError, match="Test error"):
        with transaction(db_session):
            raise ValueError("Test error")


def test_transaction_returns_session(db_session):
    """Test transaction context manager yields the session."""
    with transaction(db_session) as session:
        assert session is db_session
        assert hasattr(session, "add")
        assert hasattr(session, "commit")

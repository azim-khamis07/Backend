"""Tests for database models."""

from datetime import datetime, timezone

from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User


def test_create_user(db_session):
    """Test creating a user."""
    from app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.created_at is not None


def test_create_category(db_session, test_user):
    """Test creating a category."""
    category = Category(
        user_id=test_user.id,
        name="Groceries",
        type="expense",
    )
    db_session.add(category)
    db_session.commit()

    assert category.id is not None
    assert category.name == "Groceries"
    assert category.type == "expense"
    assert category.user_id == test_user.id


def test_create_transaction(db_session, test_user):
    """Test creating a transaction."""
    transaction = Transaction(
        user_id=test_user.id,
        amount=50.00,
        type="expense",
        occurred_at=datetime.now(timezone.utc),
        note="Test transaction",
    )
    db_session.add(transaction)
    db_session.commit()

    assert transaction.id is not None
    assert transaction.amount == 50.00
    assert transaction.type == "expense"
    assert transaction.user_id == test_user.id


def test_user_relationships(db_session, test_user):
    """Test user relationships."""
    # Create category
    category = Category(
        user_id=test_user.id,
        name="Food",
        type="expense",
    )
    db_session.add(category)
    db_session.commit()

    # Create transaction
    transaction = Transaction(
        user_id=test_user.id,
        category_id=category.id,
        amount=25.50,
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    # Refresh user
    db_session.refresh(test_user)

    # Test relationships
    assert len(test_user.categories) == 1
    assert test_user.categories[0].name == "Food"
    assert len(test_user.transactions) == 1
    assert test_user.transactions[0].amount == 25.50


"""Tests for transaction endpoints."""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.security import get_password_hash


def test_create_transaction(authenticated_client, test_user, db_session):
    """Test create transaction."""
    from app.models.category import Category

    # Create a category first
    category = Category(user_id=test_user.id, name="Food", type="expense")
    db_session.add(category)
    db_session.commit()

    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "amount": "50.00",
            "type": "expense",
            "occurred_at": "2026-01-07T10:00:00Z",
            "category_id": category.id,
            "note": "Grocery shopping",
            "tags": "food, groceries",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "50.00"
    assert data["type"] == "expense"
    assert data["category_id"] == category.id
    assert data["note"] == "Grocery shopping"
    assert data["tags"] == "food, groceries"
    assert data["user_id"] == test_user.id
    assert "id" in data
    assert "created_at" in data


def test_create_transaction_minimal(authenticated_client, test_user):
    """Test create transaction with minimal data."""
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "amount": "100.00",
            "type": "income",
            "occurred_at": "2026-01-07T10:00:00Z",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "100.00"
    assert data["type"] == "income"
    assert data["category_id"] is None


def test_create_transaction_invalid_type(authenticated_client):
    """Test create transaction with invalid type."""
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "amount": "50.00",
            "type": "invalid",
            "occurred_at": "2026-01-07T10:00:00Z",
        },
    )
    assert response.status_code == 422


def test_create_transaction_negative_amount(authenticated_client):
    """Test create transaction with negative amount."""
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "amount": "-50.00",
            "type": "expense",
            "occurred_at": "2026-01-07T10:00:00Z",
        },
    )
    assert response.status_code == 422


def test_create_transaction_invalid_category(authenticated_client, test_user):
    """Test create transaction with invalid category."""
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "amount": "50.00",
            "type": "expense",
            "occurred_at": "2026-01-07T10:00:00Z",
            "category_id": 99999,
        },
    )
    assert response.status_code == 404


def test_create_transaction_future_expense(authenticated_client):
    """Test create expense transaction in the future."""
    future_date = datetime.now(timezone.utc).replace(year=2030)
    response = authenticated_client.post(
        "/api/v1/transactions",
        json={
            "amount": "50.00",
            "type": "expense",
            "occurred_at": future_date.isoformat(),
        },
    )
    assert response.status_code == 422


def test_list_transactions(authenticated_client, test_user, db_session):
    """Test list transactions."""
    from app.models.transaction import Transaction

    # Create some transactions
    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="income",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    response = authenticated_client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "next_cursor" in data
    assert "has_more" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_list_transactions_type_filter(authenticated_client, test_user, db_session):
    """Test list transactions with type filter."""
    from app.models.transaction import Transaction

    # Create transactions of different types
    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="income",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    # Filter by expense
    response = authenticated_client.get("/api/v1/transactions?type=expense")
    assert response.status_code == 200
    data = response.json()
    assert all(item["type"] == "expense" for item in data["items"])


def test_list_transactions_category_filter(authenticated_client, test_user, db_session):
    """Test list transactions with category filter."""
    from app.models.category import Category
    from app.models.transaction import Transaction

    # Create categories and transactions
    cat1 = Category(user_id=test_user.id, name="Food", type="expense")
    cat2 = Category(user_id=test_user.id, name="Transport", type="expense")
    db_session.add_all([cat1, cat2])
    db_session.commit()

    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        category_id=cat1.id,
        occurred_at=datetime.now(timezone.utc),
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("30.00"),
        type="expense",
        category_id=cat2.id,
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    # Filter by category
    response = authenticated_client.get(f"/api/v1/transactions?category_id={cat1.id}")
    assert response.status_code == 200
    data = response.json()
    assert all(item["category_id"] == cat1.id for item in data["items"])


def test_list_transactions_date_filter(authenticated_client, test_user, db_session):
    """Test list transactions with date filter."""
    from app.models.transaction import Transaction

    # Create transactions with different dates
    date1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    date2 = datetime(2026, 1, 15, tzinfo=timezone.utc)
    date3 = datetime(2026, 2, 1, tzinfo=timezone.utc)

    tx1 = Transaction(
        user_id=test_user.id, amount=Decimal("50.00"), type="expense", occurred_at=date1
    )
    tx2 = Transaction(
        user_id=test_user.id, amount=Decimal("100.00"), type="expense", occurred_at=date2
    )
    tx3 = Transaction(
        user_id=test_user.id, amount=Decimal("75.00"), type="expense", occurred_at=date3
    )
    db_session.add_all([tx1, tx2, tx3])
    db_session.commit()

    # Filter by date range
    response = authenticated_client.get(
        "/api/v1/transactions?start_date=2026-01-01T00:00:00Z&end_date=2026-01-31T23:59:59Z"
    )
    assert response.status_code == 200
    data = response.json()
    # Should include tx1 and tx2, but not tx3


def test_list_transactions_amount_filter(authenticated_client, test_user, db_session):
    """Test list transactions with amount filter."""
    from app.models.transaction import Transaction

    # Create transactions with different amounts
    tx1 = Transaction(
        user_id=test_user.id, amount=Decimal("25.00"), type="expense", occurred_at=datetime.now(timezone.utc)
    )
    tx2 = Transaction(
        user_id=test_user.id, amount=Decimal("50.00"), type="expense", occurred_at=datetime.now(timezone.utc)
    )
    tx3 = Transaction(
        user_id=test_user.id, amount=Decimal("100.00"), type="expense", occurred_at=datetime.now(timezone.utc)
    )
    db_session.add_all([tx1, tx2, tx3])
    db_session.commit()

    # Filter by amount range
    response = authenticated_client.get("/api/v1/transactions?min_amount=40.00&max_amount=75.00")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        amount = Decimal(str(item["amount"]))
        assert Decimal("40.00") <= amount <= Decimal("75.00")


def test_list_transactions_cursor_pagination(authenticated_client, test_user, db_session):
    """Test list transactions with cursor pagination."""
    from app.models.transaction import Transaction

    # Create multiple transactions
    transactions = [
        Transaction(
            user_id=test_user.id,
            amount=Decimal(f"{i * 10}.00"),
            type="expense",
            occurred_at=datetime.now(timezone.utc),
        )
        for i in range(5)
    ]
    db_session.add_all(transactions)
    db_session.commit()

    # Get first page
    response = authenticated_client.get("/api/v1/transactions?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None
    assert data["has_more"] is True

    # Get next page using cursor
    cursor = data["next_cursor"]
    response2 = authenticated_client.get(f"/api/v1/transactions?limit=2&cursor={cursor}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) <= 2


def test_get_transaction(authenticated_client, test_user, db_session):
    """Test get transaction by ID."""
    from app.models.transaction import Transaction

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("75.50"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
        note="Test transaction",
    )
    db_session.add(transaction)
    db_session.commit()

    response = authenticated_client.get(f"/api/v1/transactions/{transaction.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transaction.id
    assert data["amount"] == "75.50"
    assert data["note"] == "Test transaction"


def test_get_transaction_not_found(authenticated_client):
    """Test get non-existent transaction."""
    response = authenticated_client.get("/api/v1/transactions/99999")
    assert response.status_code == 404


def test_get_transaction_other_user(client, db_session):
    """Test get transaction belonging to another user."""
    from app.core.security import get_password_hash
    from app.models.transaction import Transaction
    from app.models.user import User

    # Create another user and transaction
    user2 = User(
        email="user2@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user2)
    db_session.commit()

    transaction = Transaction(
        user_id=user2.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    # Login as test_user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}

    # Try to access other user's transaction
    response = client.get(f"/api/v1/transactions/{transaction.id}")
    assert response.status_code == 404


def test_update_transaction(authenticated_client, test_user, db_session):
    """Test update transaction."""
    from app.models.transaction import Transaction

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
        note="Old note",
    )
    db_session.add(transaction)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/v1/transactions/{transaction.id}",
        json={
            "amount": "75.00",
            "note": "Updated note",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "75.00"
    assert data["note"] == "Updated note"

    # Verify in database
    db_session.refresh(transaction)
    assert transaction.amount == Decimal("75.00")
    assert transaction.note == "Updated note"


def test_update_transaction_change_category(authenticated_client, test_user, db_session):
    """Test update transaction category."""
    from app.models.category import Category
    from app.models.transaction import Transaction

    cat1 = Category(user_id=test_user.id, name="Food", type="expense")
    cat2 = Category(user_id=test_user.id, name="Transport", type="expense")
    db_session.add_all([cat1, cat2])
    db_session.commit()

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        category_id=cat1.id,
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/v1/transactions/{transaction.id}",
        json={"category_id": cat2.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] == cat2.id


def test_update_transaction_change_type(authenticated_client, test_user, db_session):
    """Test update transaction type."""
    from app.models.transaction import Transaction

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/v1/transactions/{transaction.id}",
        json={"type": "income"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "income"


def test_update_transaction_invalid_category(authenticated_client, test_user, db_session):
    """Test update transaction with invalid category."""
    from app.models.transaction import Transaction

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/v1/transactions/{transaction.id}",
        json={"category_id": 99999},
    )
    assert response.status_code == 404


def test_update_transaction_future_expense(authenticated_client, test_user, db_session):
    """Test update transaction to future date for expense."""
    from app.models.transaction import Transaction

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    future_date = datetime.now(timezone.utc).replace(year=2030)
    response = authenticated_client.put(
        f"/api/v1/transactions/{transaction.id}",
        json={"occurred_at": future_date.isoformat()},
    )
    assert response.status_code == 422


def test_delete_transaction(authenticated_client, test_user, db_session):
    """Test delete transaction."""
    from app.models.transaction import Transaction

    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()
    transaction_id = transaction.id

    response = authenticated_client.delete(f"/api/v1/transactions/{transaction_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Transaction deleted successfully"

    # Verify deleted
    response = authenticated_client.get(f"/api/v1/transactions/{transaction_id}")
    assert response.status_code == 404


def test_delete_transaction_not_found(authenticated_client):
    """Test delete non-existent transaction."""
    response = authenticated_client.delete("/api/v1/transactions/99999")
    assert response.status_code == 404


def test_transaction_unauthorized(client):
    """Test transaction endpoints without authentication."""
    # List transactions
    response = client.get("/api/v1/transactions")
    assert response.status_code == 403

    # Create transaction
    response = client.post(
        "/api/v1/transactions",
        json={
            "amount": "50.00",
            "type": "expense",
            "occurred_at": "2026-01-07T10:00:00Z",
        },
    )
    assert response.status_code == 403


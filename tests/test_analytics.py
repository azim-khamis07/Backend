"""Tests for analytics endpoints."""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.security import get_password_hash


def test_get_dashboard_summary(authenticated_client, test_user, db_session):
    """Test get dashboard summary."""
    from app.models.transaction import Transaction

    # Create some transactions
    now = datetime.now(timezone.utc)
    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="income",
        occurred_at=now,
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=now,
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    # Get dashboard summary
    month = now.strftime("%Y-%m")
    response = authenticated_client.get(f"/api/v1/analytics/dashboard/summary?month={month}")
    assert response.status_code == 200
    data = response.json()
    assert "month" in data
    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_amount" in data
    assert "transaction_count" in data
    assert "top_categories" in data


def test_get_monthly_summary(authenticated_client, test_user, db_session):
    """Test get monthly summary."""
    from app.models.transaction import Transaction

    # Create transactions
    now = datetime.now(timezone.utc)
    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("200.00"),
        type="income",
        occurred_at=now,
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("75.00"),
        type="expense",
        occurred_at=now,
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    # Get monthly summary
    month = now.strftime("%Y-%m")
    response = authenticated_client.get(f"/api/v1/analytics/monthly?month={month}")
    assert response.status_code == 200
    data = response.json()
    assert data["month"] == month
    assert data["total_income"] == "200.00"
    assert data["total_expenses"] == "75.00"
    assert data["net_amount"] == "125.00"
    assert data["transaction_count"] >= 2


def test_get_category_breakdown(authenticated_client, test_user, db_session):
    """Test get category breakdown."""
    from app.models.category import Category
    from app.models.transaction import Transaction

    # Create category and transactions
    category = Category(user_id=test_user.id, name="Food", type="expense")
    db_session.add(category)
    db_session.commit()

    now = datetime.now(timezone.utc)
    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("30.00"),
        type="expense",
        category_id=category.id,
        occurred_at=now,
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="income",
        occurred_at=now,
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    # Get category breakdown
    start = now.isoformat()
    end = now.isoformat()
    response = authenticated_client.get(
        f"/api/v1/analytics/by-category?start_date={start}&end_date={end}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_income" in data
    assert "total_expenses" in data
    assert "by_category" in data
    assert len(data["by_category"]) >= 1


def test_get_cashflow(authenticated_client, test_user, db_session):
    """Test get cashflow."""
    from app.models.transaction import Transaction

    # Create transactions
    now = datetime.now(timezone.utc)
    tx1 = Transaction(
        user_id=test_user.id,
        amount=Decimal("150.00"),
        type="income",
        occurred_at=now,
    )
    tx2 = Transaction(
        user_id=test_user.id,
        amount=Decimal("60.00"),
        type="expense",
        occurred_at=now,
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    # Get cashflow
    start = now.isoformat()
    end = now.isoformat()
    response = authenticated_client.get(
        f"/api/v1/analytics/cashflow?start_date={start}&end_date={end}&interval=day"
    )
    assert response.status_code == 200
    data = response.json()
    assert "interval" in data
    assert "total_income" in data
    assert "total_expenses" in data
    assert "data" in data
    assert len(data["data"]) >= 1


def test_get_cashflow_week_interval(authenticated_client, test_user, db_session):
    """Test get cashflow with week interval."""
    from app.models.transaction import Transaction

    now = datetime.now(timezone.utc)
    tx = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="income",
        occurred_at=now,
    )
    db_session.add(tx)
    db_session.commit()

    start = now.isoformat()
    end = now.isoformat()
    response = authenticated_client.get(
        f"/api/v1/analytics/cashflow?start_date={start}&end_date={end}&interval=week"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interval"] == "week"


def test_get_cashflow_month_interval(authenticated_client, test_user, db_session):
    """Test get cashflow with month interval."""
    from app.models.transaction import Transaction

    now = datetime.now(timezone.utc)
    tx = Transaction(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        type="income",
        occurred_at=now,
    )
    db_session.add(tx)
    db_session.commit()

    start = now.isoformat()
    end = now.isoformat()
    response = authenticated_client.get(
        f"/api/v1/analytics/cashflow?start_date={start}&end_date={end}&interval=month"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interval"] == "month"


def test_analytics_unauthorized(client):
    """Test analytics endpoints without authentication."""
    # Dashboard summary
    response = client.get("/api/v1/analytics/dashboard/summary")
    assert response.status_code in [401, 403]

    # Monthly summary
    response = client.get("/api/v1/analytics/monthly?month=2026-01")
    assert response.status_code in [401, 403]

    # Category breakdown
    response = client.get("/api/v1/analytics/by-category")
    assert response.status_code in [401, 403]

    # Cashflow
    response = client.get("/api/v1/analytics/cashflow")
    assert response.status_code in [401, 403]


def test_dashboard_summary_default_month(authenticated_client, test_user, db_session):
    """Test dashboard summary defaults to current month."""
    from app.models.transaction import Transaction

    now = datetime.now(timezone.utc)
    tx = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="income",
        occurred_at=now,
    )
    db_session.add(tx)
    db_session.commit()

    # Get dashboard summary without month parameter
    response = authenticated_client.get("/api/v1/analytics/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "month" in data
    assert "total_income" in data


def test_category_breakdown_uncategorized(authenticated_client, test_user, db_session):
    """Test category breakdown includes uncategorized transactions."""
    from app.models.transaction import Transaction

    now = datetime.now(timezone.utc)
    # Create transaction without category
    tx = Transaction(
        user_id=test_user.id,
        amount=Decimal("25.00"),
        type="expense",
        occurred_at=now,
    )
    db_session.add(tx)
    db_session.commit()

    start = now.isoformat()
    end = now.isoformat()
    response = authenticated_client.get(
        f"/api/v1/analytics/by-category?start_date={start}&end_date={end}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "uncategorized_expenses" in data
    assert "uncategorized_income" in data


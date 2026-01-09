"""Tests for report endpoints."""

from datetime import datetime, timezone
from decimal import Decimal


def test_create_report(authenticated_client, test_user, db_session):
    """Test create report job."""
    from app.models.transaction import Transaction

    # Create some transactions
    transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    # Create report request
    request_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
    }

    response = authenticated_client.post("/api/v1/reports/pdf", json=request_data)

    # Should accept the request (202 Accepted)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "message" in data


def test_create_report_invalid_dates(authenticated_client):
    """Test create report with invalid dates."""
    # Invalid date format
    request_data = {
        "start_date": "invalid",
        "end_date": "2026-01-31",
    }
    response = authenticated_client.post("/api/v1/reports/pdf", json=request_data)
    assert response.status_code == 422

    # Start date after end date
    request_data = {
        "start_date": "2026-01-31",
        "end_date": "2026-01-01",
    }
    response = authenticated_client.post("/api/v1/reports/pdf", json=request_data)
    assert response.status_code == 422


def test_get_report_status(authenticated_client, test_user, db_session):
    """Test get report status."""
    from app.models.report_job import ReportJob

    # Create a report job
    job = ReportJob(
        user_id=test_user.id,
        params_json={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        status="pending",
    )
    db_session.add(job)
    db_session.commit()

    # Get status
    response = authenticated_client.get(f"/api/v1/reports/{job.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job.id
    assert data["status"] == "pending"


def test_get_report_status_not_found(authenticated_client):
    """Test get report status for non-existent job."""
    response = authenticated_client.get("/api/v1/reports/99999/status")
    assert response.status_code == 404


def test_download_report_not_completed(authenticated_client, test_user, db_session):
    """Test download report that is not completed."""
    from app.models.report_job import ReportJob

    # Create a pending job
    job = ReportJob(
        user_id=test_user.id,
        params_json={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        status="pending",
    )
    db_session.add(job)
    db_session.commit()

    # Try to download
    response = authenticated_client.get(f"/api/v1/reports/{job.id}/download")
    assert response.status_code == 422


def test_download_report_completed(authenticated_client, test_user, db_session):
    """Test download completed report."""
    from app.models.report_job import ReportJob

    # Create a completed job
    job = ReportJob(
        user_id=test_user.id,
        params_json={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        status="completed",
        s3_key="reports/test/report.pdf",
    )
    db_session.add(job)
    db_session.commit()

    # Try to download (may fail if S3 not configured)
    response = authenticated_client.get(f"/api/v1/reports/{job.id}/download")
    # May return 422 if S3 not configured, or 200 if configured
    assert response.status_code in [200, 422]
    if response.status_code == 200:
        data = response.json()
        assert "url" in data
        assert "expires_in" in data


def test_reports_unauthorized(client):
    """Test report endpoints without authentication."""
    # Create report
    request_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
    }
    response = client.post("/api/v1/reports/pdf", json=request_data)
    assert response.status_code in [401, 403]

    # Get status
    response = client.get("/api/v1/reports/1/status")
    assert response.status_code in [401, 403]

    # Download
    response = client.get("/api/v1/reports/1/download")
    assert response.status_code in [401, 403]


def test_create_report_with_filters(authenticated_client, test_user, db_session):
    """Test create report with category and type filters."""
    from app.models.category import Category
    from app.models.transaction import Transaction

    # Create category and transaction
    category = Category(
        user_id=test_user.id,
        name="Food",
        type="expense",
    )
    db_session.add(category)
    db_session.commit()

    transaction = Transaction(
        user_id=test_user.id,
        category_id=category.id,
        amount=Decimal("50.00"),
        type="expense",
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(transaction)
    db_session.commit()

    # Create report with filters
    request_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "category_ids": [category.id],
        "transaction_types": ["expense"],
    }

    response = authenticated_client.post("/api/v1/reports/pdf", json=request_data)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data


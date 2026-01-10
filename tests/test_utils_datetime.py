"""Tests for datetime utilities."""

from datetime import datetime, timedelta, timezone

from app.utils.datetime import from_isoformat, to_isoformat, to_utc, utcnow


def test_utcnow():
    """Test utcnow returns current UTC datetime."""
    result = utcnow()
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    assert result <= datetime.now(timezone.utc)


def test_to_utc_with_naive_datetime():
    """Test converting naive datetime to UTC."""
    naive_dt = datetime(2026, 1, 1, 12, 0, 0)
    result = to_utc(naive_dt)
    assert result.tzinfo == timezone.utc
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12


def test_to_utc_with_timezone_aware_datetime():
    """Test converting timezone-aware datetime to UTC."""
    # Create datetime with offset
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    result = to_utc(dt)
    assert result.tzinfo == timezone.utc
    # Should convert properly (subtract 5 hours)
    assert result.hour == 7


def test_to_utc_with_utc_datetime():
    """Test converting already UTC datetime."""
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = to_utc(dt)
    assert result.tzinfo == timezone.utc
    assert result == dt


def test_from_isoformat_with_z():
    """Test parsing ISO format string with Z."""
    iso_string = "2026-01-01T12:00:00Z"
    result = from_isoformat(iso_string)
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12


def test_from_isoformat_with_offset():
    """Test parsing ISO format string with offset."""
    iso_string = "2026-01-01T12:00:00+05:00"
    result = from_isoformat(iso_string)
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    # Should convert to UTC
    assert result.hour == 7


def test_to_isoformat():
    """Test converting datetime to ISO format string."""
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = to_isoformat(dt)
    assert isinstance(result, str)
    assert "2026-01-01T12:00:00Z" in result or "2026-01-01T12:00:00+00:00" in result


def test_to_isoformat_with_naive_datetime():
    """Test converting naive datetime to ISO format."""
    naive_dt = datetime(2026, 1, 1, 12, 0, 0)
    result = to_isoformat(naive_dt)
    assert isinstance(result, str)
    assert "2026-01-01" in result


def test_to_isoformat_with_timezone():
    """Test converting timezone-aware datetime to ISO format."""
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    result = to_isoformat(dt)
    assert isinstance(result, str)
    # Should be converted to UTC
    assert "2026-01-01" in result


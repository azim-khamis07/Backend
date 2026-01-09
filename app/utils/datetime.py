"""DateTime utilities for timezone handling."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC."""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_isoformat(iso_string: str) -> datetime:
    """Parse ISO format string to UTC datetime."""
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return to_utc(dt)


def to_isoformat(dt: datetime) -> str:
    """Convert datetime to ISO format string."""
    utc_dt = to_utc(dt)
    return utc_dt.isoformat().replace("+00:00", "Z")

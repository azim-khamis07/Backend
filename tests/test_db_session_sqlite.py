"""Tests for SQLite-specific database session functionality."""

from unittest.mock import MagicMock, patch

from app.db.session import set_sqlite_pragma


def test_set_sqlite_pragma_with_sqlite_url():
    """Test set_sqlite_pragma sets foreign keys when using SQLite."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("app.db.session.settings") as mock_settings:
        mock_settings.DATABASE_URL = "sqlite:///test.db"
        set_sqlite_pragma(mock_conn, None)
        mock_cursor.execute.assert_called_once_with("PRAGMA foreign_keys=ON")
        mock_cursor.close.assert_called_once()


def test_set_sqlite_pragma_with_postgres_url():
    """Test set_sqlite_pragma does nothing when not using SQLite."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("app.db.session.settings") as mock_settings:
        mock_settings.DATABASE_URL = "postgresql://user:pass@localhost/db"
        set_sqlite_pragma(mock_conn, None)
        mock_cursor.execute.assert_not_called()

"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.user import User

settings = get_settings()


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Create a test database session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def app(db_session: Session):
    """Create FastAPI app for testing."""
    import os
    
    # Ensure test environment settings
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
    
    # Clear settings cache to reload with test values
    from app.core.config import get_settings
    get_settings.cache_clear()
    
    app = create_app()

    # Override database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user."""
    from app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def authenticated_client(client, test_user: User):
    """Create authenticated test client."""
    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Set authorization header
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

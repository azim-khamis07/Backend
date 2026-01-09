"""Tests for authentication endpoints."""

from app.core.security import decode_token


def test_register_new_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "confirm_password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["id"] is not None


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "securepassword123",
            "confirm_password": "securepassword123",
        },
    )
    assert response.status_code == 409


def test_register_password_mismatch(client):
    """Test registration with mismatched passwords."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "confirm_password": "differentpassword123",
        },
    )
    assert response.status_code == 422


def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
            "confirm_password": "short",
        },
    )
    assert response.status_code == 422


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == test_user.email

    # Verify token
    token = data["access_token"]
    payload = decode_token(token, token_type="access")
    assert payload is not None
    assert payload["sub"] == str(test_user.id)


def test_login_invalid_email(client):
    """Test login with invalid email."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 401


def test_login_invalid_password(client, test_user):
    """Test login with invalid password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


def test_refresh_token(client, test_user):
    """Test token refresh."""
    # First login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_invalid(client):
    """Test refresh with invalid token."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"},
    )
    assert response.status_code == 401


def test_get_me(authenticated_client, test_user):
    """Test get current user."""
    response = authenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_me_unauthorized(client):
    """Test get current user without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_get_me_invalid_token(client):
    """Test get current user with invalid token."""
    client.headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


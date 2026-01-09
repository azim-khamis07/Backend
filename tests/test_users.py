"""Tests for user management endpoints."""

from app.core.security import get_password_hash, verify_password


def test_get_me(authenticated_client, test_user):
    """Test get current user profile."""
    response = authenticated_client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["is_active"] == test_user.is_active


def test_get_me_unauthorized(client):
    """Test get current user without authentication."""
    response = client.get("/api/v1/users/me")
    assert response.status_code in [401, 403]


def test_update_profile_email(authenticated_client, test_user, db_session):
    """Test update user profile email."""
    new_email = "updated@example.com"
    response = authenticated_client.put(
        "/api/v1/users/me",
        json={"email": new_email},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email
    assert data["id"] == test_user.id

    # Verify in database
    db_session.refresh(test_user)
    assert test_user.email == new_email


def test_update_profile_no_changes(authenticated_client, test_user):
    """Test update user profile with no changes."""
    original_email = test_user.email
    response = authenticated_client.put(
        "/api/v1/users/me",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == original_email


def test_update_profile_duplicate_email(client, db_session):
    """Test update profile with duplicate email."""
    from app.models.user import User

    # Create another user
    user2 = User(
        email="user2@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user2)
    db_session.commit()

    # Create test user first
    from app.core.security import get_password_hash
    test_user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(test_user)
    db_session.commit()

    # Login as first user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}

    # Try to update to user2's email
    response = client.put(
        "/api/v1/users/me",
        json={"email": "user2@example.com"},
    )
    assert response.status_code == 409


def test_update_profile_invalid_email(authenticated_client):
    """Test update profile with invalid email."""
    response = authenticated_client.put(
        "/api/v1/users/me",
        json={"email": "invalid-email"},
    )
    assert response.status_code == 422


def test_change_password_success(authenticated_client, test_user, db_session):
    """Test successful password change."""
    new_password = "newpassword123"
    response = authenticated_client.post(
        "/api/v1/users/me/password",
        json={
            "current_password": "testpassword123",
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Password changed successfully"

    # Verify password was changed
    db_session.refresh(test_user)
    assert verify_password(new_password, test_user.password_hash)
    assert not verify_password("testpassword123", test_user.password_hash)


def test_change_password_wrong_current(authenticated_client):
    """Test password change with wrong current password."""
    response = authenticated_client.post(
        "/api/v1/users/me/password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert response.status_code == 422


def test_change_password_mismatch(authenticated_client):
    """Test password change with mismatched new passwords."""
    response = authenticated_client.post(
        "/api/v1/users/me/password",
        json={
            "current_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword123",
        },
    )
    assert response.status_code == 422


def test_change_password_weak_password(authenticated_client):
    """Test password change with weak password."""
    response = authenticated_client.post(
        "/api/v1/users/me/password",
        json={
            "current_password": "testpassword123",
            "new_password": "short",
            "confirm_password": "short",
        },
    )
    assert response.status_code == 422


def test_change_password_unauthorized(client):
    """Test password change without authentication."""
    response = client.post(
        "/api/v1/users/me/password",
        json={
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert response.status_code in [401, 403]

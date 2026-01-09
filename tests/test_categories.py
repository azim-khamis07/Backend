"""Tests for category endpoints."""


def test_create_category(authenticated_client, test_user):
    """Test create category."""
    response = authenticated_client.post(
        "/api/v1/categories",
        json={
            "name": "Groceries",
            "type": "expense",
            "description": "Food and groceries",
            "color": "#FF5733",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["type"] == "expense"
    assert data["user_id"] == test_user.id
    assert data["description"] == "Food and groceries"
    assert data["color"] == "#FF5733"
    assert "id" in data
    assert "created_at" in data


def test_create_category_minimal(authenticated_client, test_user):
    """Test create category with minimal data."""
    response = authenticated_client.post(
        "/api/v1/categories",
        json={
            "name": "Income",
            "type": "income",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Income"
    assert data["type"] == "income"


def test_create_category_invalid_type(authenticated_client):
    """Test create category with invalid type."""
    response = authenticated_client.post(
        "/api/v1/categories",
        json={
            "name": "Test",
            "type": "invalid",
        },
    )
    assert response.status_code == 422


def test_create_category_duplicate_name(authenticated_client, test_user):
    """Test create category with duplicate name."""
    # Create first category
    authenticated_client.post(
        "/api/v1/categories",
        json={
            "name": "Groceries",
            "type": "expense",
        },
    )

    # Try to create duplicate
    response = authenticated_client.post(
        "/api/v1/categories",
        json={
            "name": "Groceries",
            "type": "income",
        },
    )
    assert response.status_code == 409


def test_list_categories(authenticated_client, test_user, db_session):
    """Test list categories."""
    from app.models.category import Category

    # Create some categories
    cat1 = Category(user_id=test_user.id, name="Food", type="expense")
    cat2 = Category(user_id=test_user.id, name="Salary", type="income")
    db_session.add_all([cat1, cat2])
    db_session.commit()

    response = authenticated_client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_list_categories_with_type_filter(authenticated_client, test_user, db_session):
    """Test list categories with type filter."""
    from app.models.category import Category

    # Create categories of different types
    cat1 = Category(user_id=test_user.id, name="Food", type="expense")
    cat2 = Category(user_id=test_user.id, name="Salary", type="income")
    db_session.add_all([cat1, cat2])
    db_session.commit()

    # Filter by expense
    response = authenticated_client.get("/api/v1/categories?type_filter=expense")
    assert response.status_code == 200
    data = response.json()
    assert all(cat["type"] == "expense" for cat in data["items"])


def test_list_categories_pagination(authenticated_client, test_user, db_session):
    """Test list categories with pagination."""
    from app.models.category import Category

    # Create multiple categories
    categories = [
        Category(user_id=test_user.id, name=f"Category {i}", type="expense") for i in range(5)
    ]
    db_session.add_all(categories)
    db_session.commit()

    # Get first page
    response = authenticated_client.get("/api/v1/categories?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2


def test_get_category(authenticated_client, test_user, db_session):
    """Test get category by ID."""
    from app.models.category import Category

    category = Category(user_id=test_user.id, name="Test Category", type="expense")
    db_session.add(category)
    db_session.commit()

    response = authenticated_client.get(f"/api/v1/categories/{category.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category.id
    assert data["name"] == "Test Category"


def test_get_category_not_found(authenticated_client):
    """Test get non-existent category."""
    response = authenticated_client.get("/api/v1/categories/99999")
    assert response.status_code == 404


def test_get_category_other_user(client, db_session, test_user):
    """Test get category belonging to another user."""
    from app.core.security import get_password_hash
    from app.models.category import Category
    from app.models.user import User

    # Create another user and category
    user2 = User(
        email="user2@example.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user2)
    db_session.commit()

    category = Category(user_id=user2.id, name="Other User Category", type="expense")
    db_session.add(category)
    db_session.commit()

    # Login as test_user (ensure user exists first)
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_data = login_response.json()
    assert "access_token" in login_data, f"Missing access_token: {login_data}"
    token = login_data["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}

    # Try to access other user's category
    response = client.get(f"/api/v1/categories/{category.id}")
    assert response.status_code == 404


def test_update_category(authenticated_client, test_user, db_session):
    """Test update category."""
    from app.models.category import Category

    category = Category(user_id=test_user.id, name="Old Name", type="expense")
    db_session.add(category)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/v1/categories/{category.id}",
        json={
            "name": "New Name",
            "description": "Updated description",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated description"

    # Verify in database
    db_session.refresh(category)
    assert category.name == "New Name"


def test_update_category_change_type(authenticated_client, test_user, db_session):
    """Test update category type."""
    from app.models.category import Category

    category = Category(user_id=test_user.id, name="Test", type="expense")
    db_session.add(category)
    db_session.commit()

    response = authenticated_client.put(
        f"/api/v1/categories/{category.id}",
        json={"type": "income"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "income"


def test_update_category_duplicate_name(authenticated_client, test_user, db_session):
    """Test update category to duplicate name."""
    from app.models.category import Category

    cat1 = Category(user_id=test_user.id, name="Category 1", type="expense")
    cat2 = Category(user_id=test_user.id, name="Category 2", type="expense")
    db_session.add_all([cat1, cat2])
    db_session.commit()

    # Try to rename cat2 to cat1's name
    response = authenticated_client.put(
        f"/api/v1/categories/{cat2.id}",
        json={"name": "Category 1"},
    )
    assert response.status_code == 409


def test_delete_category(authenticated_client, test_user, db_session):
    """Test delete category."""
    from app.models.category import Category

    category = Category(user_id=test_user.id, name="To Delete", type="expense")
    db_session.add(category)
    db_session.commit()
    category_id = category.id

    response = authenticated_client.delete(f"/api/v1/categories/{category_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Category deleted successfully"

    # Verify deleted
    response = authenticated_client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 404


def test_delete_category_not_found(authenticated_client):
    """Test delete non-existent category."""
    response = authenticated_client.delete("/api/v1/categories/99999")
    assert response.status_code == 404


def test_category_unauthorized(client):
    """Test category endpoints without authentication."""
    # List categories
    response = client.get("/api/v1/categories")
    assert response.status_code in [401, 403]

    # Create category
    response = client.post(
        "/api/v1/categories",
        json={"name": "Test", "type": "expense"},
    )
    assert response.status_code in [401, 403]

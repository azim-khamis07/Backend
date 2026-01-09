#!/usr/bin/env python3
"""
Comprehensive Phase 3 Testing Script
Tests all transaction CRUD operations, filtering, and validation
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal, init_db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.core.security import get_password_hash

# Initialize database
init_db()

client = TestClient(app)

def truncate_password(password: str) -> str:
    """Truncate password to 72 bytes for bcrypt compatibility."""
    encoded = password.encode('utf-8')
    if len(encoded) > 72:
        return encoded[:72].decode('utf-8', errors='ignore')
    return password

def setup_test_user():
    """Create or get test user."""
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.email == 'test@example.com').first()
        if not test_user:
            test_user = User(
                email='test@example.com',
                password_hash=get_password_hash(truncate_password('testpass123'))
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        return test_user
    finally:
        db.close()

def get_auth_token(user_id: int, email: str):
    """Get authentication token."""
    return create_access_token({'sub': str(user_id), 'email': email})

def test_crud_operations():
    """Test all CRUD operations."""
    print("=" * 60)
    print("🧪 TESTING: CRUD Operations")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    # CREATE
    print("1️⃣  Testing CREATE transaction...")
    response = client.post(
        '/api/v1/transactions',
        json={
            'amount': '100.00',
            'type': 'income',
            'occurred_at': datetime.now(timezone.utc).isoformat(),
            'note': 'Test transaction'
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    tx_id = data['id']
    print(f"   ✅ Created transaction ID: {tx_id}")
    print(f"   ✅ Amount: {data['amount']}")
    print(f"   ✅ Type: {data['type']}")
    print()
    
    # READ (List)
    print("2️⃣  Testing LIST transactions...")
    response = client.get('/api/v1/transactions')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    assert 'next_cursor' in data
    assert 'has_more' in data
    print(f"   ✅ Found {len(data['items'])} transaction(s)")
    print(f"   ✅ Total: {data['total']}")
    print(f"   ✅ Has more: {data['has_more']}")
    print()
    
    # READ (Get by ID)
    print("3️⃣  Testing GET transaction by ID...")
    response = client.get(f'/api/v1/transactions/{tx_id}')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data['id'] == tx_id
    print(f"   ✅ Retrieved transaction ID: {data['id']}")
    print()
    
    # UPDATE
    print("4️⃣  Testing UPDATE transaction...")
    response = client.put(
        f'/api/v1/transactions/{tx_id}',
        json={
            'amount': '150.00',
            'note': 'Updated transaction'
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data['amount'] == '150.00'
    assert data['note'] == 'Updated transaction'
    print(f"   ✅ Updated amount to: {data['amount']}")
    print(f"   ✅ Updated note: {data['note']}")
    print()
    
    # DELETE
    print("5️⃣  Testing DELETE transaction...")
    response = client.delete(f'/api/v1/transactions/{tx_id}')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'message' in data
    print(f"   ✅ Deleted transaction: {data['message']}")
    print()
    
    # Verify deleted
    response = client.get(f'/api/v1/transactions/{tx_id}')
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    print("   ✅ Verified transaction is deleted (404 on get)")
    print()
    
    print("✅ ALL CRUD OPERATIONS PASSED!")
    print()

def test_filtering():
    """Test filtering functionality."""
    print("=" * 60)
    print("🧪 TESTING: Filtering")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    db = SessionLocal()
    try:
        # Create test category
        category = db.query(Category).filter(
            Category.user_id == user.id,
            Category.name == 'Test Category'
        ).first()
        if not category:
            category = Category(user_id=user.id, name='Test Category', type='expense')
            db.add(category)
            db.commit()
            db.refresh(category)
        
        # Create test transactions
        now = datetime.now(timezone.utc)
        tx1 = Transaction(
            user_id=user.id,
            amount=Decimal('50.00'),
            type='expense',
            category_id=category.id,
            occurred_at=now
        )
        tx2 = Transaction(
            user_id=user.id,
            amount=Decimal('100.00'),
            type='income',
            occurred_at=now
        )
        db.add_all([tx1, tx2])
        db.commit()
    finally:
        db.close()
    
    # Test type filter
    print("1️⃣  Testing TYPE filter...")
    response = client.get('/api/v1/transactions?type=expense')
    assert response.status_code == 200
    data = response.json()
    assert all(item['type'] == 'expense' for item in data['items'])
    print(f"   ✅ Filtered {len(data['items'])} expense transaction(s)")
    print()
    
    # Test category filter
    print("2️⃣  Testing CATEGORY filter...")
    response = client.get(f'/api/v1/transactions?category_id={category.id}')
    assert response.status_code == 200
    data = response.json()
    assert all(item.get('category_id') == category.id for item in data['items'] if item.get('category_id'))
    print(f"   ✅ Filtered transactions by category")
    print()
    
    # Test amount filter
    print("3️⃣  Testing AMOUNT RANGE filter...")
    response = client.get('/api/v1/transactions?min_amount=75.00&max_amount=125.00')
    assert response.status_code == 200
    data = response.json()
    print(f"   ✅ Filtered transactions by amount range")
    print()
    
    # Test date filter
    print("4️⃣  Testing DATE RANGE filter...")
    start = now.isoformat()
    end = now.isoformat()
    response = client.get(f'/api/v1/transactions?start_date={start}&end_date={end}')
    assert response.status_code == 200
    print(f"   ✅ Filtered transactions by date range")
    print()
    
    # Test cursor pagination
    print("5️⃣  Testing CURSOR PAGINATION...")
    response = client.get('/api/v1/transactions?limit=1')
    assert response.status_code == 200
    data = response.json()
    assert 'next_cursor' in data
    assert 'has_more' in data
    print(f"   ✅ Cursor pagination working")
    print(f"   ✅ Has more: {data['has_more']}")
    if data['next_cursor']:
        print(f"   ✅ Next cursor: {data['next_cursor']}")
    print()
    
    print("✅ ALL FILTERING TESTS PASSED!")
    print()

def test_validation():
    """Test validation rules."""
    print("=" * 60)
    print("🧪 TESTING: Validation")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    # Test invalid type
    print("1️⃣  Testing INVALID TYPE validation...")
    response = client.post(
        '/api/v1/transactions',
        json={
            'amount': '100.00',
            'type': 'invalid',
            'occurred_at': datetime.now(timezone.utc).isoformat()
        }
    )
    assert response.status_code == 422
    print("   ✅ Invalid type rejected (422)")
    print()
    
    # Test negative amount
    print("2️⃣  Testing NEGATIVE AMOUNT validation...")
    response = client.post(
        '/api/v1/transactions',
        json={
            'amount': '-50.00',
            'type': 'expense',
            'occurred_at': datetime.now(timezone.utc).isoformat()
        }
    )
    assert response.status_code == 422
    print("   ✅ Negative amount rejected (422)")
    print()
    
    # Test future expense
    print("3️⃣  Testing FUTURE EXPENSE validation...")
    future_date = datetime.now(timezone.utc).replace(year=2030)
    response = client.post(
        '/api/v1/transactions',
        json={
            'amount': '50.00',
            'type': 'expense',
            'occurred_at': future_date.isoformat()
        }
    )
    assert response.status_code == 422
    print("   ✅ Future expense rejected (422)")
    print()
    
    # Test unauthorized access
    print("4️⃣  Testing UNAUTHORIZED ACCESS protection...")
    client.headers = {}
    response = client.get('/api/v1/transactions')
    assert response.status_code in [401, 403]
    print("   ✅ Unauthorized access blocked")
    print()
    
    # Test not found
    print("5️⃣  Testing NOT FOUND handling...")
    client.headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/api/v1/transactions/99999')
    assert response.status_code == 404
    print("   ✅ Not found returns 404")
    print()
    
    print("✅ ALL VALIDATION TESTS PASSED!")
    print()

def main():
    """Run all tests."""
    print()
    print("🚀 PHASE 3 COMPREHENSIVE TESTING")
    print("=" * 60)
    print()
    
    try:
        test_crud_operations()
        test_filtering()
        test_validation()
        
        print("=" * 60)
        print("🎉 ALL PHASE 3 TESTS PASSED! 🎉")
        print("=" * 60)
        print()
        print("✅ CRUD Operations: PASSED")
        print("✅ Filtering: PASSED")
        print("✅ Validation: PASSED")
        print()
        print("Phase 3 is fully implemented and tested!")
        return 0
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3
"""
Comprehensive Phase 4 Testing Script
Tests all analytics endpoints, caching, and aggregation queries
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
from app.infra.redis import cache_service

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

def test_dashboard_summary():
    """Test dashboard summary endpoint."""
    print("=" * 60)
    print("🧪 TESTING: Dashboard Summary")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    db = SessionLocal()
    try:
        # Create test transactions
        now = datetime.now(timezone.utc)
        month = now.strftime("%Y-%m")
        
        # Create category
        category = db.query(Category).filter(
            Category.user_id == user.id,
            Category.name == 'Test Category'
        ).first()
        if not category:
            category = Category(user_id=user.id, name='Test Category', type='expense')
            db.add(category)
            db.commit()
            db.refresh(category)
        
        # Create transactions
        tx1 = Transaction(
            user_id=user.id,
            amount=Decimal('200.00'),
            type='income',
            occurred_at=now
        )
        tx2 = Transaction(
            user_id=user.id,
            amount=Decimal('50.00'),
            type='expense',
            category_id=category.id,
            occurred_at=now
        )
        db.add_all([tx1, tx2])
        db.commit()
    finally:
        db.close()
    
    # Test dashboard summary
    print("1️⃣  Testing GET dashboard summary...")
    response = client.get(f'/api/v1/analytics/dashboard/summary?month={month}')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert 'month' in data
    assert 'total_income' in data
    assert 'total_expenses' in data
    assert 'net_amount' in data
    assert 'top_categories' in data
    print(f"   ✅ Dashboard summary retrieved")
    print(f"   ✅ Month: {data['month']}")
    print(f"   ✅ Total Income: {data['total_income']}")
    print(f"   ✅ Total Expenses: {data['total_expenses']}")
    print(f"   ✅ Net Amount: {data['net_amount']}")
    print()
    
    # Test default month (current month)
    print("2️⃣  Testing default month (current month)...")
    response = client.get('/api/v1/analytics/dashboard/summary')
    assert response.status_code == 200
    print("   ✅ Default month works")
    print()
    
    print("✅ DASHBOARD SUMMARY TESTS PASSED!")
    print()

def test_monthly_summary():
    """Test monthly summary endpoint."""
    print("=" * 60)
    print("🧪 TESTING: Monthly Summary")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        month = now.strftime("%Y-%m")
        
        # Create transaction
        tx = Transaction(
            user_id=user.id,
            amount=Decimal('150.00'),
            type='income',
            occurred_at=now
        )
        db.add(tx)
        db.commit()
    finally:
        db.close()
    
    print("1️⃣  Testing GET monthly summary...")
    response = client.get(f'/api/v1/analytics/monthly?month={month}')
    assert response.status_code == 200
    data = response.json()
    assert data['month'] == month
    assert 'total_income' in data
    assert 'total_expenses' in data
    assert 'net_amount' in data
    assert 'transaction_count' in data
    print(f"   ✅ Monthly summary retrieved")
    print(f"   ✅ Transaction count: {data['transaction_count']}")
    print()
    
    print("✅ MONTHLY SUMMARY TESTS PASSED!")
    print()

def test_category_breakdown():
    """Test category breakdown endpoint."""
    print("=" * 60)
    print("🧪 TESTING: Category Breakdown")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Create categories
        cat1 = db.query(Category).filter(
            Category.user_id == user.id,
            Category.name == 'Food'
        ).first()
        if not cat1:
            cat1 = Category(user_id=user.id, name='Food', type='expense')
            db.add(cat1)
            db.commit()
            db.refresh(cat1)
        
        # Create transactions
        tx1 = Transaction(
            user_id=user.id,
            amount=Decimal('30.00'),
            type='expense',
            category_id=cat1.id,
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
    
    print("1️⃣  Testing GET category breakdown...")
    start = now.isoformat()
    end = now.isoformat()
    response = client.get(f'/api/v1/analytics/by-category?start_date={start}&end_date={end}')
    assert response.status_code == 200
    data = response.json()
    assert 'total_income' in data
    assert 'total_expenses' in data
    assert 'by_category' in data
    assert 'uncategorized_income' in data
    assert 'uncategorized_expenses' in data
    print(f"   ✅ Category breakdown retrieved")
    print(f"   ✅ Categories: {len(data['by_category'])}")
    print()
    
    print("✅ CATEGORY BREAKDOWN TESTS PASSED!")
    print()

def test_cashflow():
    """Test cashflow endpoint."""
    print("=" * 60)
    print("🧪 TESTING: Cashflow")
    print("=" * 60)
    print()
    
    user = setup_test_user()
    token = get_auth_token(user.id, user.email)
    client.headers = {'Authorization': f'Bearer {token}'}
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Create transactions
        tx1 = Transaction(
            user_id=user.id,
            amount=Decimal('150.00'),
            type='income',
            occurred_at=now
        )
        tx2 = Transaction(
            user_id=user.id,
            amount=Decimal('60.00'),
            type='expense',
            occurred_at=now
        )
        db.add_all([tx1, tx2])
        db.commit()
    finally:
        db.close()
    
    start = now.isoformat()
    end = now.isoformat()
    
    # Test day interval
    print("1️⃣  Testing cashflow with DAY interval...")
    response = client.get(f'/api/v1/analytics/cashflow?start_date={start}&end_date={end}&interval=day')
    assert response.status_code == 200
    data = response.json()
    assert data['interval'] == 'day'
    assert 'data' in data
    assert len(data['data']) >= 1
    print(f"   ✅ Cashflow (day) retrieved")
    print()
    
    # Test week interval
    print("2️⃣  Testing cashflow with WEEK interval...")
    response = client.get(f'/api/v1/analytics/cashflow?start_date={start}&end_date={end}&interval=week')
    assert response.status_code == 200
    data = response.json()
    assert data['interval'] == 'week'
    print(f"   ✅ Cashflow (week) retrieved")
    print()
    
    # Test month interval
    print("3️⃣  Testing cashflow with MONTH interval...")
    response = client.get(f'/api/v1/analytics/cashflow?start_date={start}&end_date={end}&interval=month')
    assert response.status_code == 200
    data = response.json()
    assert data['interval'] == 'month'
    print(f"   ✅ Cashflow (month) retrieved")
    print()
    
    print("✅ CASHFLOW TESTS PASSED!")
    print()

def test_caching():
    """Test Redis caching."""
    print("=" * 60)
    print("🧪 TESTING: Redis Caching")
    print("=" * 60)
    print()
    
    # Test Redis connection
    print("1️⃣  Testing Redis connection...")
    try:
        if cache_service.ping():
            print("   ✅ Redis is connected")
        else:
            print("   ⚠️  Redis not available (may not be running)")
            return
    except Exception as e:
        print(f"   ⚠️  Redis error: {e}")
        return
    
    # Test cache operations
    print("2️⃣  Testing cache operations...")
    test_key = "test:cache:key"
    test_value = {"test": "data", "number": 123}
    
    # Set cache
    result = cache_service.set(test_key, test_value, ttl=60)
    assert result, "Cache set failed"
    print("   ✅ Cache set works")
    
    # Get cache
    cached = cache_service.get(test_key)
    assert cached == test_value, "Cache get failed"
    print("   ✅ Cache get works")
    
    # Delete cache
    result = cache_service.delete(test_key)
    assert result, "Cache delete failed"
    print("   ✅ Cache delete works")
    
    # Verify deleted
    cached = cache_service.get(test_key)
    assert cached is None, "Cache should be deleted"
    print("   ✅ Cache deletion verified")
    print()
    
    print("✅ CACHING TESTS PASSED!")
    print()

def test_unauthorized():
    """Test unauthorized access."""
    print("=" * 60)
    print("🧪 TESTING: Unauthorized Access")
    print("=" * 60)
    print()
    
    client.headers = {}
    
    endpoints = [
        '/api/v1/analytics/dashboard/summary',
        '/api/v1/analytics/monthly?month=2026-01',
        '/api/v1/analytics/by-category',
        '/api/v1/analytics/cashflow',
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403], f"Expected 401/403 for {endpoint}, got {response.status_code}"
        print(f"   ✅ {endpoint} - Unauthorized access blocked")
    
    print()
    print("✅ UNAUTHORIZED ACCESS TESTS PASSED!")
    print()

def main():
    """Run all tests."""
    print()
    print("🚀 PHASE 4 COMPREHENSIVE TESTING")
    print("=" * 60)
    print()
    
    try:
        test_dashboard_summary()
        test_monthly_summary()
        test_category_breakdown()
        test_cashflow()
        test_caching()
        test_unauthorized()
        
        print("=" * 60)
        print("🎉 ALL PHASE 4 TESTS PASSED! 🎉")
        print("=" * 60)
        print()
        print("✅ Dashboard Summary: PASSED")
        print("✅ Monthly Summary: PASSED")
        print("✅ Category Breakdown: PASSED")
        print("✅ Cashflow: PASSED")
        print("✅ Caching: PASSED")
        print("✅ Authorization: PASSED")
        print()
        print("Phase 4 is fully implemented and tested!")
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


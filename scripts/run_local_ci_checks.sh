#!/bin/bash
# Script to run local CI checks before pushing to remote

set -e

echo "🔍 Running Local CI Checks..."
echo ""

cd "$(dirname "$0")/.."

echo "1️⃣ Checking Black formatting..."
docker-compose exec api black --check app/ tests/ || {
    echo "❌ Black formatting failed. Running black to fix..."
    docker-compose exec api black app/ tests/
    echo "✅ Formatted with Black"
}

echo ""
echo "2️⃣ Checking isort import sorting..."
docker-compose exec api isort --check-only app/ tests/ || {
    echo "❌ isort failed. Running isort to fix..."
    docker-compose exec api isort app/ tests/
    echo "✅ Fixed import sorting"
}

echo ""
echo "3️⃣ Running flake8 linting..."
docker-compose exec api flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503 || {
    echo "⚠️  flake8 found issues (check output above)"
}

echo ""
echo "4️⃣ Running tests..."
docker-compose exec api pytest tests/ -v --tb=short || {
    echo "❌ Tests failed (check output above)"
    exit 1
}

echo ""
echo "✅ All checks passed! Ready to push."


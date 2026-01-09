#!/bin/bash
# Code Quality Check Script
# Runs all code quality checks

set -e

echo "🔍 Running Code Quality Checks..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated. Activating...${NC}"
    source venv/bin/activate
fi

# 1. Code Formatting (Black)
echo -e "${GREEN}1. Checking code formatting (black)...${NC}"
if black --check app/ tests/; then
    echo -e "${GREEN}✅ Black: OK${NC}"
else
    echo -e "${RED}❌ Black: FAILED${NC}"
    echo "Run: black app/ tests/"
    exit 1
fi
echo ""

# 2. Import Sorting (isort)
echo -e "${GREEN}2. Checking import sorting (isort)...${NC}"
if isort --check-only app/ tests/; then
    echo -e "${GREEN}✅ isort: OK${NC}"
else
    echo -e "${RED}❌ isort: FAILED${NC}"
    echo "Run: isort app/ tests/"
    exit 1
fi
echo ""

# 3. Linting (flake8)
echo -e "${GREEN}3. Running linter (flake8)...${NC}"
if flake8 app/ tests/ --max-line-length=100 --exclude=__pycache__,migrations --count --statistics; then
    echo -e "${GREEN}✅ flake8: OK${NC}"
else
    echo -e "${YELLOW}⚠️  flake8: Found issues (non-blocking)${NC}"
fi
echo ""

# 4. Type Checking (mypy)
echo -e "${GREEN}4. Running type checker (mypy)...${NC}"
if mypy app/ --ignore-missing-imports; then
    echo -e "${GREEN}✅ mypy: OK${NC}"
else
    echo -e "${YELLOW}⚠️  mypy: Found issues (non-blocking)${NC}"
fi
echo ""

# 5. Security Scan (bandit)
echo -e "${GREEN}5. Running security scan (bandit)...${NC}"
if bandit -r app/ -f json -o bandit-report.json; then
    echo -e "${GREEN}✅ bandit: OK${NC}"
else
    echo -e "${YELLOW}⚠️  bandit: Found issues (check bandit-report.json)${NC}"
fi
echo ""

# 6. Tests with Coverage
echo -e "${GREEN}6. Running tests with coverage...${NC}"
if pytest --cov=app --cov-report=term-missing --cov-report=html -v; then
    echo -e "${GREEN}✅ Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Tests: FAILED${NC}"
    exit 1
fi
echo ""

# 7. Coverage Threshold
echo -e "${GREEN}7. Checking coverage threshold (80%)...${NC}"
if coverage report --fail-under=80; then
    echo -e "${GREEN}✅ Coverage: >= 80%${NC}"
else
    echo -e "${RED}❌ Coverage: < 80%${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}🎉 All quality checks passed!${NC}"


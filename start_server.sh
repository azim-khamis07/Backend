#!/bin/bash
# Quick server startup script

set -e

echo "🚀 Starting Expense Tracker API Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if PostgreSQL is running
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "📦 Starting PostgreSQL and Redis..."
    docker-compose up -d postgres redis
    sleep 3
fi

# Initialize database if needed
echo "🗄️  Checking database..."
python -c "
from app.db.session import init_db
try:
    init_db()
    print('✓ Database tables ready')
except Exception as e:
    print(f'⚠ Database may already exist: {e}')
"

echo ""
echo "🌟 Starting FastAPI server..."

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use. Stopping existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
    sleep 2
    echo "✅ Port 8000 cleared"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 Documentation URLs:"
echo "   • Swagger UI:  http://localhost:8000/docs"
echo "   • ReDoc:       http://localhost:8000/redoc"
echo "   • Health:      http://localhost:8000/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


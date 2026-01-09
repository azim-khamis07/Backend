#!/bin/bash
# Script to debug and kill processes using port 8000

set -e

echo "🔍 Debugging Port 8000 Issue"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Find what's using port 8000
echo "📋 Step 1: Finding processes using port 8000..."
echo ""

if lsof -i :8000 2>/dev/null; then
    echo ""
    echo "Found processes using port 8000:"
    lsof -i :8000
else
    echo "No processes found with lsof"
fi

echo ""
echo "Checking with netstat/ss..."
if command -v ss >/dev/null 2>&1; then
    ss -tulpn | grep :8000 || echo "No processes found with ss"
elif command -v netstat >/dev/null 2>&1; then
    netstat -tulpn 2>/dev/null | grep :8000 || echo "No processes found with netstat"
fi

echo ""
echo "Checking for uvicorn processes..."
ps aux | grep -E "uvicorn|app.main" | grep -v grep || echo "No uvicorn processes found"

echo ""
echo "Checking Docker containers..."
docker ps -a | grep -E "backend-api|8000" || echo "No Docker containers using port 8000"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Stop Docker containers
echo "🛑 Step 2: Stopping Docker containers..."
docker-compose down --remove-orphans 2>/dev/null || true
echo "✅ Docker containers stopped"

# Step 3: Kill processes on port 8000
echo ""
echo "🛑 Step 3: Killing processes on port 8000..."

# Method 1: Using lsof
if lsof -ti:8000 >/dev/null 2>&1; then
    PIDS=$(lsof -ti:8000)
    echo "Found PIDs: $PIDS"
    echo "$PIDS" | xargs kill -9 2>/dev/null && echo "✅ Killed processes using lsof"
else
    echo "⚠️  No processes found with lsof"
fi

# Method 2: Kill uvicorn processes
if pgrep -f "uvicorn.*app.main" >/dev/null 2>&1; then
    pkill -9 -f "uvicorn.*app.main" 2>/dev/null && echo "✅ Killed uvicorn processes"
else
    echo "⚠️  No uvicorn processes found"
fi

# Method 3: Force kill with fuser
if command -v fuser >/dev/null 2>&1; then
    fuser -k 8000/tcp 2>/dev/null && echo "✅ Force killed with fuser" || echo "⚠️  fuser found nothing"
fi

# Wait a moment
sleep 2

# Step 4: Verify port is free
echo ""
echo "✅ Step 4: Verifying port 8000 is free..."
if lsof -i :8000 >/dev/null 2>&1; then
    echo "❌ ERROR: Port 8000 is still in use!"
    echo "Remaining processes:"
    lsof -i :8000
    exit 1
else
    echo "✅ SUCCESS: Port 8000 is now FREE!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Port 8000 is ready to use!"
echo ""
echo "You can now start the server with:"
echo "  ./start_server.sh"
echo "  OR"
echo "  docker-compose up"
echo ""


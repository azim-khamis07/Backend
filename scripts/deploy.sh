#!/bin/bash
#
# Production Deployment Script
# Usage: ./scripts/deploy.sh [environment]
#

set -e  # Exit on error

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "🚀 Starting deployment to $ENVIRONMENT environment..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose installed${NC}"

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please update .env with production values before continuing${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ .env file exists${NC}"

# Check if .env has production values
if grep -q "dev-secret-key" .env || grep -q "devpassword" .env; then
    echo -e "${RED}❌ .env file contains development values. Please update with production values${NC}"
    exit 1
fi

echo ""
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo ""
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ Waiting for API to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ API failed to become healthy${NC}"
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.prod.yml logs api --tail=50
    exit 1
fi

echo ""
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔗 Service URLs:"
echo "   API: http://localhost:8000"
echo "   Health: http://localhost:8000/health"
echo "   Docs: http://localhost:8000/docs"
echo "   Metrics: http://localhost:8000/metrics"

echo ""
echo "📝 View logs with:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"


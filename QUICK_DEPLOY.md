# Quick Deployment Guide

## 🚀 Fastest Way to Deploy

### Prerequisites
- Docker and Docker Compose installed
- Production environment variables ready

### Steps

1. **Clone and Setup**
   ```bash
   git clone <your-repo-url>
   cd expense-tracker-backend
   cp .env.example .env
   # Edit .env with your production values
   ```

2. **Deploy**
   ```bash
   ./scripts/deploy.sh production
   ```

3. **Verify**
   ```bash
   curl http://localhost:8000/health
   ```

That's it! 🎉

## 📋 Manual Deployment

If you prefer manual steps:

```bash
# 1. Build images
docker-compose -f docker-compose.prod.yml build

# 2. Start services
docker-compose -f docker-compose.prod.yml up -d

# 3. Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# 4. Check health
curl http://localhost:8000/health
```

## 🔧 Common Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update and redeploy
git pull
./scripts/deploy.sh production
```

For detailed deployment instructions, see `DEPLOYMENT_PLAN.md`.

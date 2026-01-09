# Deployment Plan & Guide

**Version:** 1.0  
**Last Updated:** 2026-01-08  
**Status:** Production Ready

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Deployment Options](#deployment-options)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Prerequisites

- [ ] **Code Repository**: Code pushed to Git (GitHub/GitLab)
- [ ] **Database**: PostgreSQL instance ready (managed or self-hosted)
- [ ] **Cache**: Redis instance ready (managed or self-hosted)
- [ ] **Storage**: AWS S3 bucket created (or compatible object storage)
- [ ] **Domain**: Domain name configured (optional but recommended)
- [ ] **SSL Certificate**: SSL/TLS certificate ready (Let's Encrypt recommended)
- [ ] **Secrets**: All secrets generated and secured
- [ ] **Backup Strategy**: Backup procedures documented and tested

### ✅ Security Checklist

- [ ] **SECRET_KEY**: Strong random key (min 32 characters)
- [ ] **Database Credentials**: Strong passwords
- [ ] **AWS Credentials**: IAM user with minimal permissions
- [ ] **CORS Origins**: Configured for production domains
- [ ] **Rate Limiting**: Enabled and configured
- [ ] **Security Headers**: Verified in production
- [ ] **HTTPS**: SSL/TLS configured
- [ ] **Environment Variables**: All secrets in secure storage

### ✅ Testing Checklist

- [ ] **Unit Tests**: All tests passing
- [ ] **Integration Tests**: All tests passing
- [ ] **Load Testing**: Basic load testing completed
- [ ] **Security Scan**: Dependency vulnerabilities checked
- [ ] **Database Migrations**: Tested on staging

---

## Infrastructure Requirements

### Minimum Requirements

| Component | Specification | Notes |
|-----------|--------------|-------|
| **API Server** | 2 CPU, 2GB RAM | Can scale horizontally |
| **Database** | 2 CPU, 4GB RAM, 20GB storage | Managed PostgreSQL recommended |
| **Redis** | 1 CPU, 1GB RAM | Managed Redis recommended |
| **S3 Storage** | 10GB initial | Scales automatically |
| **Network** | HTTPS enabled | Load balancer recommended |

### Recommended Production Setup

- **API Servers**: 2-4 instances behind load balancer
- **Database**: Managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
- **Redis**: Managed Redis (AWS ElastiCache, Redis Cloud, etc.)
- **Storage**: AWS S3 with versioning enabled
- **CDN**: CloudFront or similar for static assets (optional)
- **Monitoring**: Prometheus + Grafana or cloud monitoring
- **Error Tracking**: Sentry configured

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Small/Medium Scale)

**Best for:**
- Single server deployments
- Small to medium traffic
- Full control over infrastructure

**Pros:**
- Simple setup
- Easy to manage
- All services in one place

**Cons:**
- Single point of failure
- Manual scaling
- Requires server management

### Option 2: Cloud Platform (Recommended for Production)

**Best for:**
- Production deployments
- High availability requirements
- Auto-scaling needs

**Supported Platforms:**
- **Render**: Easy deployment, managed services
- **AWS ECS/Fargate**: Enterprise-grade, scalable
- **Google Cloud Run**: Serverless, auto-scaling
- **Heroku**: Simple, managed platform
- **DigitalOcean App Platform**: Simple, cost-effective

### Option 3: Kubernetes (Advanced)

**Best for:**
- Large scale deployments
- Multi-region deployments
- Complex orchestration needs

---

## Step-by-Step Deployment

### Method 1: Docker Compose Deployment

#### Step 1: Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### Step 2: Clone Repository

```bash
# Clone repository
git clone https://github.com/yourusername/expense-tracker-backend.git
cd expense-tracker-backend

# Checkout production branch (if applicable)
git checkout production
```

#### Step 3: Create Production Environment File

```bash
# Create .env file
cat > .env << 'EOF'
# Application
ENVIRONMENT=production
DEBUG=false
APP_NAME=Expense Tracker API
APP_VERSION=1.0.0

# Security
SECRET_KEY=your-very-long-random-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (use managed database in production)
DATABASE_URL=postgresql://user:password@db-host:5432/expensedb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis (use managed Redis in production)
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/1
CELERY_RESULT_BACKEND=redis://redis-host:6379/2
REDIS_CACHE_TTL=1800

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name

# CORS (update with your frontend domain)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Sentry (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

# Secure the .env file
chmod 600 .env
```

#### Step 4: Create Production Docker Compose File

```bash
# Create docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # FastAPI App
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    image: expense-tracker-backend:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    image: expense-tracker-backend:latest
    restart: unless-stopped
    command: celery -A app.infra.queue worker --loglevel=info --concurrency=4
    env_file:
      - .env
    environment:
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    networks:
      - app-network

  # PostgreSQL (use managed database in production)
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: expensedb
      POSTGRES_USER: expenseuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U expenseuser -d expensedb"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (use managed Redis in production)
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
EOF
```

#### Step 5: Build and Start Services

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api
```

#### Step 6: Run Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Verify migration
docker-compose -f docker-compose.prod.yml exec api alembic current
```

#### Step 7: Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics

# Check API docs
curl http://localhost:8000/docs
```

---

### Method 2: Render Deployment

#### Step 1: Prepare Repository

```bash
# Ensure all code is committed
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

#### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure service:
   - **Name**: `expense-tracker-api`
   - **Environment**: `Docker`
   - **Region**: Choose closest to users
   - **Branch**: `main` or `production`
   - **Root Directory**: `.` (root)

#### Step 3: Configure Environment Variables

In Render dashboard, add all environment variables from `.env`:

```
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
# ... (all other variables)
```

#### Step 4: Add PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `expense-tracker-db`
   - **Database**: `expensedb`
   - **User**: `expenseuser`
3. Copy **Internal Database URL**
4. Update `DATABASE_URL` in Web Service environment variables

#### Step 5: Add Redis Instance

1. Click **"New +"** → **"Redis"**
2. Configure:
   - **Name**: `expense-tracker-redis`
3. Copy **Internal Redis URL**
4. Update `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` in Web Service

#### Step 6: Deploy

1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Monitor deployment logs
3. Wait for deployment to complete

#### Step 7: Run Migrations

```bash
# SSH into Render service (if available) or use Render Shell
# Or add migration as a build command in Render settings
alembic upgrade head
```

#### Step 8: Add Celery Worker

1. Click **"New +"** → **"Background Worker"**
2. Configure:
   - **Name**: `expense-tracker-worker`
   - **Environment**: `Docker`
   - **Command**: `celery -A app.infra.queue worker --loglevel=info`
3. Use same environment variables as Web Service
4. Deploy

---

### Method 3: AWS ECS/Fargate Deployment

#### Step 1: Build and Push Docker Image

```bash
# Configure AWS CLI
aws configure

# Create ECR repository
aws ecr create-repository --repository-name expense-tracker-backend

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t expense-tracker-backend:latest -f docker/Dockerfile .

# Tag image
docker tag expense-tracker-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/expense-tracker-backend:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/expense-tracker-backend:latest
```

#### Step 2: Create ECS Task Definition

1. Go to **ECS** → **Task Definitions** → **Create new Task Definition**
2. Configure:
   - **Task Definition Name**: `expense-tracker-api`
   - **Launch Type**: `Fargate`
   - **Task Role**: Create IAM role with necessary permissions
   - **Task Memory**: `2 GB`
   - **Task CPU**: `1 vCPU`
3. Add Container:
   - **Container Name**: `api`
   - **Image**: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/expense-tracker-backend:latest`
   - **Port Mappings**: `8000:8000`
   - **Environment Variables**: Add all from `.env`
   - **Health Check**: 
     - Command: `CMD-SHELL,curl -f http://localhost:8000/health || exit 1`
     - Interval: `30`
     - Timeout: `5`
     - Retries: `3`

#### Step 3: Create ECS Service

1. Go to **ECS** → **Clusters** → **Create Cluster**
2. Configure:
   - **Cluster Name**: `expense-tracker-cluster`
   - **Infrastructure**: `AWS Fargate`
3. Create Service:
   - **Task Definition**: Select created task definition
   - **Service Name**: `expense-tracker-api`
   - **Desired Count**: `2` (for high availability)
   - **Load Balancer**: Create Application Load Balancer
   - **Target Group**: Create new target group
   - **Health Check**: `/health`

#### Step 4: Configure RDS Database

1. Create RDS PostgreSQL instance
2. Configure security groups to allow ECS access
3. Update `DATABASE_URL` in ECS task definition

#### Step 5: Configure ElastiCache Redis

1. Create ElastiCache Redis cluster
2. Configure security groups
3. Update Redis URLs in ECS task definition

#### Step 6: Deploy

1. Update task definition with new image
2. Update service to use new task definition
3. ECS will automatically deploy new tasks

---

## Post-Deployment Verification

### 1. Health Check

```bash
# Check API health
curl https://api.yourdomain.com/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Expense Tracker API",
#   "version": "1.0.0",
#   "redis": "connected",
#   "database": "connected"
# }
```

### 2. API Documentation

```bash
# Check Swagger docs
curl https://api.yourdomain.com/docs

# Should return HTML with API documentation
```

### 3. Test Authentication

```bash
# Register a test user
curl -X POST https://api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!"
  }'

# Login
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

### 4. Check Metrics

```bash
# Prometheus metrics
curl https://api.yourdomain.com/metrics

# Should return Prometheus-formatted metrics
```

### 5. Verify Security Headers

```bash
# Check security headers
curl -I https://api.yourdomain.com/health

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 6. Test Rate Limiting

```bash
# Make multiple rapid requests
for i in {1..10}; do
  curl -X POST https://api.yourdomain.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}'
done

# Should eventually return 429 Too Many Requests
```

---

## Monitoring & Maintenance

### 1. Application Monitoring

#### Health Checks

Set up automated health checks:

```bash
# Cron job for health monitoring
*/5 * * * * curl -f https://api.yourdomain.com/health || echo "API is down" | mail -s "API Alert" admin@example.com
```

#### Prometheus Metrics

If using Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'expense-tracker-api'
    static_configs:
      - targets: ['api.yourdomain.com:8000']
    metrics_path: '/metrics'
```

#### Sentry Error Tracking

Errors are automatically tracked if `SENTRY_DSN` is configured.

### 2. Log Monitoring

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f api

# Or in cloud platforms, use their log viewer
```

### 3. Database Monitoring

- Monitor connection pool usage
- Check slow queries
- Monitor database size
- Set up alerts for high CPU/memory

### 4. Redis Monitoring

- Monitor memory usage
- Check cache hit rates
- Monitor connection count

### 5. Regular Maintenance Tasks

#### Daily
- [ ] Check application health
- [ ] Review error logs
- [ ] Monitor resource usage

#### Weekly
- [ ] Review application logs
- [ ] Check disk space
- [ ] Review security alerts
- [ ] Check backup status

#### Monthly
- [ ] Update dependencies
- [ ] Review and optimize database queries
- [ ] Security patches
- [ ] Review metrics and performance

#### Quarterly
- [ ] Security audit
- [ ] Architecture review
- [ ] Capacity planning
- [ ] Disaster recovery test

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Symptoms:**
- `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions:**
```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
docker-compose -f docker-compose.prod.yml exec api python -c "from app.db.session import engine; engine.connect()"
```

#### 2. Redis Connection Errors

**Symptoms:**
- `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions:**
```bash
# Check Redis is running
docker-compose -f docker-compose.prod.yml ps redis

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec api python -c "from app.infra.redis import cache_service; print(cache_service.ping())"
```

#### 3. S3 Upload Failures

**Symptoms:**
- `botocore.exceptions.ClientError: Access Denied`

**Solutions:**
- Verify AWS credentials
- Check IAM permissions
- Verify bucket exists and is accessible
- Check bucket region matches `AWS_REGION`

#### 4. Celery Tasks Not Running

**Symptoms:**
- Reports not generating
- Tasks stuck in queue

**Solutions:**
```bash
# Check worker is running
docker-compose -f docker-compose.prod.yml ps worker

# Check worker logs
docker-compose -f docker-compose.prod.yml logs worker

# Verify broker connection
docker-compose -f docker-compose.prod.yml exec worker celery -A app.infra.queue inspect active
```

#### 5. High Memory Usage

**Symptoms:**
- Application crashes
- Slow responses

**Solutions:**
- Increase container memory
- Review query optimization
- Check for memory leaks
- Reduce worker count if needed

#### 6. Rate Limiting Too Strict

**Symptoms:**
- Legitimate users getting 429 errors

**Solutions:**
- Adjust `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_PER_HOUR`
- Review rate limit logs
- Consider per-user rate limiting

---

## Rollback Procedure

### Quick Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Rollback database migrations (if needed)
docker-compose -f docker-compose.prod.yml exec api alembic downgrade -1
```

### Cloud Platform Rollback

1. Go to platform dashboard
2. Find previous successful deployment
3. Click "Rollback" or redeploy previous version
4. Verify health after rollback

---

## Security Best Practices

1. ✅ **Never commit `.env` files** to version control
2. ✅ **Use secrets management** (AWS Secrets Manager, HashiCorp Vault)
3. ✅ **Rotate secrets regularly** (every 90 days)
4. ✅ **Use HTTPS** for all API communication
5. ✅ **Enable rate limiting** to prevent abuse
6. ✅ **Monitor for security vulnerabilities** regularly
7. ✅ **Keep dependencies updated**
8. ✅ **Use least privilege** for IAM roles
9. ✅ **Enable database encryption** at rest
10. ✅ **Regular security audits**

---

## Support & Resources

- **Documentation**: See `README.md`, `ARCHITECTURE.md`
- **Migration Guide**: See `MIGRATION_STRATEGY.md`
- **Backup Guide**: See `BACKUP_STRATEGY.md`
- **API Documentation**: `https://api.yourdomain.com/docs`

---

**Last Updated**: 2026-01-08  
**Maintained By**: Development Team


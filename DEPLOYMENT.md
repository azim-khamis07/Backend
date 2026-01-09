# Deployment Guide

This guide covers deploying the Expense Tracker Backend to production.

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- PostgreSQL database (managed or self-hosted)
- Redis instance (managed or self-hosted)
- AWS S3 bucket (for file storage)
- Domain name and SSL certificate (for HTTPS)

## Environment Setup

### 1. Environment Variables

Create a `.env` file with production values:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/1
CELERY_RESULT_BACKEND=redis://host:6379/2

# Security
SECRET_KEY=your-secret-key-min-32-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name

# Application
ENVIRONMENT=production
DEBUG=false
API_V1_PREFIX=/api/v1
```

### 2. Database Setup

#### Create Database

```sql
CREATE DATABASE expensedb;
CREATE USER expenseuser WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE expensedb TO expenseuser;
```

#### Run Migrations

```bash
alembic upgrade head
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Small/Medium Scale)

1. **Update docker-compose.yml** with production settings

2. **Build and start services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

### Option 2: Docker (Standalone)

1. **Build image**
   ```bash
   docker build -t expense-tracker-backend:latest -f docker/Dockerfile .
   ```

2. **Run container**
   ```bash
   docker run -d \
     --name expense-tracker-api \
     -p 8000:8000 \
     --env-file .env \
     expense-tracker-backend:latest
   ```

### Option 3: Cloud Platforms

#### Render

1. Create a new Web Service
2. Connect your GitHub repository
3. Set environment variables
4. Deploy

#### AWS ECS/Fargate

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Create ECS service
4. Configure load balancer

#### Heroku

1. Create Heroku app
2. Add PostgreSQL and Redis addons
3. Set environment variables
4. Deploy via Git

## Production Configuration

### 1. Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. SSL/TLS

Use Let's Encrypt for free SSL certificates:

```bash
certbot --nginx -d api.yourdomain.com
```

### 3. Process Management

Use systemd for process management:

```ini
[Unit]
Description=Expense Tracker API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/expense-tracker-backend
Environment="PATH=/opt/expense-tracker-backend/venv/bin"
ExecStart=/opt/expense-tracker-backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Celery Worker

```ini
[Unit]
Description=Expense Tracker Celery Worker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/expense-tracker-backend
Environment="PATH=/opt/expense-tracker-backend/venv/bin"
ExecStart=/opt/expense-tracker-backend/venv/bin/celery -A app.infra.queue worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring

### Health Checks

The application provides a health endpoint:

```bash
curl http://localhost:8000/health
```

### Logging

- **Location**: Application logs (stdout/stderr)
- **Format**: JSON structured logging
- **Level**: INFO in production, DEBUG in development

### Metrics (Future)

- Prometheus metrics endpoint
- Application performance monitoring
- Error tracking (Sentry)

## Scaling

### Horizontal Scaling

1. **API Servers**: Run multiple instances behind load balancer
2. **Database**: Use read replicas for read-heavy workloads
3. **Redis**: Use Redis Cluster for high availability
4. **Celery Workers**: Scale workers based on queue depth

### Vertical Scaling

1. **Database**: Increase memory and CPU
2. **Redis**: Increase memory allocation
3. **Application**: Increase worker count

## Backup Strategy

### Database Backups

```bash
# Daily backup
pg_dump -U expenseuser expensedb > backup_$(date +%Y%m%d).sql

# Restore
psql -U expenseuser expensedb < backup_20260108.sql
```

### S3 Backups

- Enable S3 versioning
- Configure lifecycle policies
- Regular backup verification

## Security Checklist

- [ ] Strong SECRET_KEY (min 32 characters, random)
- [ ] HTTPS enabled
- [ ] Database credentials secured
- [ ] AWS credentials with minimal permissions
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Security headers set
- [ ] Regular dependency updates
- [ ] Security scanning enabled

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify network connectivity
   - Check firewall rules

2. **Redis Connection Errors**
   - Verify REDIS_URL
   - Check Redis is running
   - Verify network access

3. **S3 Upload Failures**
   - Verify AWS credentials
   - Check bucket permissions
   - Verify bucket exists

4. **Celery Tasks Not Running**
   - Check worker is running
   - Verify broker connection
   - Check task logs

## Rollback Procedure

1. **Stop new deployments**
2. **Revert to previous Docker image**
3. **Rollback database migrations** (if needed)
   ```bash
   alembic downgrade -1
   ```
4. **Restart services**
5. **Verify health**

## Maintenance

### Regular Tasks

- **Weekly**: Review logs, check disk space
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Review and optimize database queries
- **Annually**: Security audit, architecture review

---

**Last Updated**: 2026-01-08


# Improved Deployment Plan - Multi-Environment Setup

**Version:** 2.0  
**Last Updated:** 2026-01-08  
**Status:** Production Ready with Multi-Environment Support

---

## 🎯 Overview

This improved deployment plan implements **professional multi-environment architecture** with separate configurations for **dev**, **staging**, and **production** environments.

---

## 🏗️ Architecture

### Environment Structure

```
terraform/environments/
├── dev/          # Development environment
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars.example
│   └── README.md
├── staging/     # Staging environment
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars.example
│   └── README.md
└── production/   # Production environment
    ├── main.tf
    ├── variables.tf
    ├── terraform.tfvars.example
    └── README.md
```

### Deployment Flow

```
Feature Branch
    ↓
Pull Request → CI Tests
    ↓
Merge to develop → Auto-deploy to DEV
    ↓
Test & Validate in DEV
    ↓
Manual Deploy to STAGING (optional)
    ↓
Test & QA in STAGING
    ↓
Merge to main → Auto-deploy to PRODUCTION
```

---

## 🚀 Quick Start

### Option 1: Deploy All Environments

```bash
# Deploy development
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init && terraform apply

# Deploy staging
cd ../staging
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init && terraform apply

# Deploy production
cd ../production
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init && terraform apply
```

### Option 2: Use Deployment Script

```bash
# Deploy to specific environment
./scripts/deploy_environment.sh dev
./scripts/deploy_environment.sh staging
./scripts/deploy_environment.sh production
```

---

## 📋 Environment Comparison

### Development Environment

**Purpose**: Active development and testing

**Infrastructure**:
- VPC: `10.1.0.0/16`
- RDS: `db.t3.micro` (single AZ)
- Redis: `cache.t3.micro`
- ECS: 0.5 vCPU, 1GB, 1 task
- NAT Gateway: ❌ Disabled
- **Cost**: ~$51/month

**Deployment**:
- Automatic on push to `develop`
- Manual via workflow dispatch

### Staging Environment

**Purpose**: Pre-production testing

**Infrastructure**:
- VPC: `10.2.0.0/16`
- RDS: `db.t3.small` (single AZ)
- Redis: `cache.t3.small`
- ECS: 1 vCPU, 2GB, 2 tasks
- NAT Gateway: ✅ Enabled
- **Cost**: ~$130/month

**Deployment**:
- Manual via workflow dispatch
- Optional: Auto on `develop` merge

### Production Environment

**Purpose**: Live production

**Infrastructure**:
- VPC: `10.0.0.0/16`
- RDS: `db.t3.small` (multi-AZ optional)
- Redis: `cache.t3.small`
- ECS: 1 vCPU, 2GB, 2+ tasks
- NAT Gateway: ✅ Enabled
- **Cost**: ~$130/month

**Deployment**:
- Automatic on push to `main`
- Manual via workflow dispatch (with approval)

---

## 🔄 CI/CD Pipeline Updates

### Automatic Deployments

| Branch | Environment | Trigger |
|--------|-------------|---------|
| `develop` | dev | On push |
| `main` | production | On push |

### Manual Deployments

Use GitHub Actions workflow dispatch:

1. Go to **Actions** → **CD** → **Run workflow**
2. Select environment: `dev`, `staging`, or `production`
3. Click **Run workflow**

### Infrastructure Changes

Include `[terraform]` in commit message to trigger infrastructure updates:

```bash
git commit -m "[terraform] Update RDS instance size"
git push origin main
```

---

## 🔐 Secret Management

### Per-Environment Secrets

Configure secrets per environment in GitHub:

**Repository Secrets** (shared):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_ACCOUNT_ID`

**Environment-Specific** (via GitHub Environments):
- `DATABASE_URL_DEV` / `DATABASE_URL_STAGING` / `DATABASE_URL_PRODUCTION`
- `REDIS_URL_DEV` / `REDIS_URL_STAGING` / `REDIS_URL_PRODUCTION`
- `SECRET_KEY_DEV` / `SECRET_KEY_STAGING` / `SECRET_KEY_PRODUCTION`

### Setting Up GitHub Environments

1. Go to **Settings** → **Environments**
2. Create: `dev`, `staging`, `production`
3. Add environment-specific secrets
4. Set protection rules (e.g., require approval for production)

---

## 💰 Cost Optimization

### Development Environment Savings

- **No NAT Gateway**: Saves ~$35/month
- **Smaller instances**: Saves ~$20/month
- **Single task**: Saves ~$15/month
- **Total**: ~$70/month savings vs production

### Total Monthly Cost

- **Dev**: ~$51/month
- **Staging**: ~$130/month
- **Production**: ~$130/month
- **Total**: ~$311/month

---

## 📊 Deployment Commands

### Deploy Infrastructure

```bash
# Using script
./scripts/deploy_environment.sh dev
./scripts/deploy_environment.sh staging
./scripts/deploy_environment.sh production

# Manual
cd terraform/environments/<env>
terraform init
terraform plan
terraform apply
```

### Update Application Only

```bash
# Force new deployment
aws ecs update-service \
  --cluster expense-tracker-cluster-<env> \
  --service expense-tracker-api-<env> \
  --force-new-deployment
```

### Get Environment URLs

```bash
# Dev
cd terraform/environments/dev && terraform output alb_dns_name

# Staging
cd terraform/environments/staging && terraform output alb_dns_name

# Production
cd terraform/environments/production && terraform output alb_dns_name
```

---

## ✅ Best Practices

### 1. Environment Isolation

- ✅ Separate VPCs (different CIDR blocks)
- ✅ Separate databases
- ✅ Separate Redis instances
- ✅ Separate S3 buckets
- ✅ Separate ECR repositories

### 2. Deployment Strategy

- ✅ Always test in dev first
- ✅ Use staging for final validation
- ✅ Promote through environments
- ✅ Never skip staging for critical changes

### 3. Secret Management

- ✅ Different secrets per environment
- ✅ Use GitHub Environments
- ✅ Never commit secrets
- ✅ Rotate secrets regularly

### 4. Cost Management

- ✅ Optimize dev environment
- ✅ Monitor costs per environment
- ✅ Use smaller instances for dev
- ✅ Disable unnecessary services in dev

### 5. Monitoring

- ✅ Separate dashboards per environment
- ✅ Environment-specific alerts
- ✅ Different log retention
- ✅ Cost tracking per environment

---

## 🎯 Migration from Single to Multi-Environment

If you have existing production infrastructure:

1. **Backup current state**
   ```bash
   cd terraform/environments/production
   terraform state pull > production-backup.json
   ```

2. **Create dev environment**
   ```bash
   cd terraform/environments/dev
   terraform init && terraform apply
   ```

3. **Create staging environment**
   ```bash
   cd terraform/environments/staging
   terraform init && terraform apply
   ```

4. **Update CD workflow** (already updated)

5. **Test deployments**
   - Push to `develop` → deploys to dev
   - Push to `main` → deploys to production

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `MULTI_ENVIRONMENT_DEPLOYMENT.md` | Complete multi-env guide |
| `ENVIRONMENT_STRATEGY.md` | Environment strategy & best practices |
| `COMPLETE_DEPLOYMENT_GUIDE.md` | Step-by-step deployment |
| `CICD_SETUP_PLAN.md` | CI/CD setup details |
| `DEPLOYMENT_CHECKLIST.md` | Deployment checklist |

---

## 🎉 Key Improvements

✅ **Three separate environments**: dev, staging, production  
✅ **Isolated infrastructure**: Separate VPCs, databases, caches  
✅ **Cost-optimized dev**: ~$70/month savings  
✅ **Automatic deployments**: Based on branch  
✅ **Manual deployments**: Via workflow dispatch  
✅ **Environment promotion**: Dev → Staging → Production  
✅ **Professional setup**: Industry best practices  

---

**Last Updated**: 2026-01-08


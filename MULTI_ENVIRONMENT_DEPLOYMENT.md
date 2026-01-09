# Multi-Environment Deployment Guide

**Version:** 2.0  
**Last Updated:** 2026-01-08  
**Status:** Production Ready

---

## Overview

This guide covers the professional multi-environment deployment setup with separate configurations for **dev**, **staging**, and **production** environments.

---

## Environment Strategy

### Environment Tiers

| Environment | Branch | Purpose | Infrastructure Size | Auto-Deploy |
|------------|--------|---------|---------------------|-------------|
| **dev** | `develop` or manual | Development & testing | Small (cost-optimized) | On push to `develop` |
| **staging** | `develop` or manual | Pre-production testing | Medium | On push to `develop` |
| **production** | `main` | Live production | Full scale | On push to `main` |

### Infrastructure Differences

#### Development Environment
- **VPC CIDR**: `10.1.0.0/16`
- **RDS**: `db.t3.micro` (single AZ)
- **Redis**: `cache.t3.micro`
- **ECS**: 0.5 vCPU, 1GB RAM, 1 task
- **NAT Gateway**: Disabled (cost savings)
- **Multi-AZ**: Disabled

#### Staging Environment
- **VPC CIDR**: `10.2.0.0/16`
- **RDS**: `db.t3.small` (single AZ)
- **Redis**: `cache.t3.small`
- **ECS**: 1 vCPU, 2GB RAM, 2 tasks
- **NAT Gateway**: Enabled
- **Multi-AZ**: Disabled

#### Production Environment
- **VPC CIDR**: `10.0.0.0/16`
- **RDS**: `db.t3.small` (multi-AZ optional)
- **Redis**: `cache.t3.small`
- **ECS**: 1 vCPU, 2GB RAM, 2+ tasks
- **NAT Gateway**: Enabled
- **Multi-AZ**: Enabled (optional)

---

## Setup Instructions

### Step 1: Create All Environments

#### Development Environment

```bash
cd terraform/environments/dev

# Create configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with dev values
nano terraform.tfvars

# Initialize and apply
terraform init
terraform plan
terraform apply
```

#### Staging Environment

```bash
cd terraform/environments/staging

# Create configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with staging values
nano terraform.tfvars

# Initialize and apply
terraform init
terraform plan
terraform apply
```

#### Production Environment

```bash
cd terraform/environments/production

# Create configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with production values
nano terraform.tfvars

# Initialize and apply
terraform init
terraform plan
terraform apply
```

---

## CI/CD Pipeline Behavior

### Automatic Deployments

#### Push to `develop` branch
```
develop branch → Deploy to DEV
```

#### Push to `main` branch
```
main branch → Deploy to PRODUCTION
```

### Manual Deployments

Use GitHub Actions workflow dispatch to deploy to any environment:

1. Go to **Actions** → **CD** → **Run workflow**
2. Select environment: `dev`, `staging`, or `production`
3. Click **Run workflow**

### Infrastructure Changes

To deploy infrastructure changes, include `[terraform]` in commit message:

```bash
git commit -m "[terraform] Update RDS instance size"
git push origin main
```

This triggers Terraform apply in the CD workflow.

---

## Environment Promotion Workflow

### Recommended Flow

```
Feature Branch
    ↓
Pull Request → CI Tests
    ↓
Merge to develop → Deploy to DEV
    ↓
Test in DEV
    ↓
Merge to main → Deploy to STAGING (optional)
    ↓
Test in STAGING
    ↓
Deploy to PRODUCTION
```

### Promotion Commands

```bash
# Promote dev → staging
cd terraform/environments/staging
terraform apply -var="app_image_tag=dev-latest"

# Promote staging → production
cd terraform/environments/production
terraform apply -var="app_image_tag=staging-latest"
```

---

## Environment-Specific Configurations

### Development Environment

**File**: `terraform/environments/dev/terraform.tfvars`

```hcl
aws_region = "us-east-1"
project_name = "expense-tracker"
vpc_cidr = "10.1.0.0/16"

# Smaller instances for cost savings
db_password = "dev-password"
secret_key = "dev-secret-key-32-chars-minimum"
```

**Characteristics:**
- Cost-optimized
- Single instance
- No NAT Gateway
- Smaller database

### Staging Environment

**File**: `terraform/environments/staging/terraform.tfvars`

```hcl
aws_region = "us-east-1"
project_name = "expense-tracker"
vpc_cidr = "10.2.0.0/16"

# Production-like but smaller
db_password = "staging-password"
secret_key = "staging-secret-key-32-chars-minimum"
rds_instance_class = "db.t3.small"
ecs_desired_count = 2
```

**Characteristics:**
- Production-like setup
- Multiple instances
- Full networking
- Testing environment

### Production Environment

**File**: `terraform/environments/production/terraform.tfvars`

```hcl
aws_region = "us-east-1"
project_name = "expense-tracker"
vpc_cidr = "10.0.0.0/16"

# Full production setup
db_password = "strong-production-password"
secret_key = "strong-production-secret-key-32-chars"
rds_instance_class = "db.t3.small"
rds_multi_az = true  # High availability
ecs_desired_count = 2
```

**Characteristics:**
- Full scale
- High availability
- Multi-AZ database
- Production-grade security

---

## GitHub Secrets Configuration

### Environment-Specific Secrets

You can use GitHub Environments to manage secrets per environment:

1. Go to **Settings** → **Environments**
2. Create environments: `dev`, `staging`, `production`
3. Add environment-specific secrets

### Shared Secrets (Repository Level)

These apply to all environments:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `AWS_ACCOUNT_ID`

### Environment-Specific Secrets

Add these per environment:

| Secret | Dev | Staging | Production |
|--------|-----|---------|------------|
| `DATABASE_URL` | dev DB | staging DB | prod DB |
| `REDIS_URL` | dev Redis | staging Redis | prod Redis |
| `SECRET_KEY` | dev key | staging key | prod key |
| `SENTRY_DSN` | dev DSN | staging DSN | prod DSN |

---

## Deployment Commands

### Deploy to Specific Environment

```bash
# Deploy to dev
cd terraform/environments/dev
terraform apply

# Deploy to staging
cd terraform/environments/staging
terraform apply

# Deploy to production
cd terraform/environments/production
terraform apply
```

### Update Application Only (No Infrastructure)

```bash
# Update ECS service in dev
aws ecs update-service \
  --cluster expense-tracker-cluster-dev \
  --service expense-tracker-api-dev \
  --force-new-deployment

# Update ECS service in staging
aws ecs update-service \
  --cluster expense-tracker-cluster-staging \
  --service expense-tracker-api-staging \
  --force-new-deployment

# Update ECS service in production
aws ecs update-service \
  --cluster expense-tracker-cluster-production \
  --service expense-tracker-api-production \
  --force-new-deployment
```

---

## Cost Comparison

### Monthly Costs (Approximate)

| Component | Dev | Staging | Production | Total |
|-----------|-----|---------|------------|-------|
| ECS Fargate | ~$8 | ~$30 | ~$30 | ~$68 |
| RDS | ~$15 | ~$30 | ~$30 | ~$75 |
| ElastiCache | ~$8 | ~$15 | ~$15 | ~$38 |
| ALB | ~$20 | ~$20 | ~$20 | ~$60 |
| NAT Gateway | $0 | ~$35 | ~$35 | ~$70 |
| **Total** | **~$51** | **~$130** | **~$130** | **~$311** |

*Note: Dev environment saves ~$35/month by not using NAT Gateway*

---

## Best Practices

### 1. Environment Isolation

- ✅ Separate VPCs for each environment
- ✅ Different CIDR blocks (10.0.x.x, 10.1.x.x, 10.2.x.x)
- ✅ Separate databases
- ✅ Separate Redis instances
- ✅ Separate S3 buckets

### 2. Secret Management

- ✅ Different secrets per environment
- ✅ Use GitHub Environments for secrets
- ✅ Never commit secrets to Git
- ✅ Rotate secrets regularly

### 3. Deployment Strategy

- ✅ Always test in dev first
- ✅ Promote through staging before production
- ✅ Use feature flags for gradual rollouts
- ✅ Monitor each environment separately

### 4. Cost Optimization

- ✅ Use smaller instances for dev
- ✅ Disable NAT Gateway in dev
- ✅ Single-AZ for dev/staging
- ✅ Auto-scale down during off-hours (optional)

### 5. Monitoring

- ✅ Separate CloudWatch dashboards per environment
- ✅ Environment-specific alerts
- ✅ Different log retention periods
- ✅ Cost tracking per environment

---

## Troubleshooting

### Environment-Specific Issues

#### Dev Environment

```bash
# Check dev resources
cd terraform/environments/dev
terraform state list

# View dev logs
aws logs tail /ecs/expense-tracker-api-dev --follow
```

#### Staging Environment

```bash
# Check staging resources
cd terraform/environments/staging
terraform state list

# View staging logs
aws logs tail /ecs/expense-tracker-api-staging --follow
```

#### Production Environment

```bash
# Check production resources
cd terraform/environments/production
terraform state list

# View production logs
aws logs tail /ecs/expense-tracker-api-production --follow
```

---

## Migration from Single to Multi-Environment

If you already have a production environment:

1. **Backup current state**
   ```bash
   cd terraform/environments/production
   terraform state pull > production-state-backup.json
   ```

2. **Create dev environment**
   ```bash
   cd terraform/environments/dev
   terraform init
   terraform apply
   ```

3. **Create staging environment**
   ```bash
   cd terraform/environments/staging
   terraform init
   terraform apply
   ```

4. **Update CD workflow** (already done)

5. **Test deployments**
   - Push to `develop` → should deploy to dev
   - Push to `main` → should deploy to production

---

## Quick Reference

### Environment URLs

After deployment, get URLs:

```bash
# Dev
cd terraform/environments/dev
terraform output alb_dns_name

# Staging
cd terraform/environments/staging
terraform output alb_dns_name

# Production
cd terraform/environments/production
terraform output alb_dns_name
```

### Common Commands

```bash
# List all environments
ls terraform/environments/

# Switch between environments
cd terraform/environments/<env>

# Get outputs for specific environment
terraform output -json

# Destroy environment (careful!)
terraform destroy
```

---

## Summary

✅ **Three separate environments**: dev, staging, production  
✅ **Isolated infrastructure**: Separate VPCs, databases, caches  
✅ **Automatic deployments**: Based on branch  
✅ **Manual deployments**: Via workflow dispatch  
✅ **Cost-optimized dev**: Smaller instances, no NAT  
✅ **Production-ready**: Full scale, high availability  

---

**Last Updated**: 2026-01-08


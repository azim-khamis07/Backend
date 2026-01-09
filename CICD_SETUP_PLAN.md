# CI/CD Setup Plan - AWS ECS/Fargate Deployment

**Version:** 1.0  
**Last Updated:** 2026-01-08  
**Status:** Implementation Guide

---

## Overview

This plan provides step-by-step instructions to set up a complete CI/CD pipeline that:
- Runs CI on every push/PR (lint, format, typecheck, tests, Docker build, security scans)
- Runs CD on merge to main (build, tag, push to ECR, Terraform apply, deploy to ECS/Fargate)
- Implements rolling updates with health checks

---

## Architecture Flow

```
Developer Push/PR
      |
      v
GitHub Actions (CI)
  ├─ Lint/Format/Typecheck
  ├─ Unit + Integration Tests
  ├─ Build Docker Images
  └─ Security Scans
      |
      v
On Merge to Main (CD)
  ├─ Build + Tag Images
  ├─ Push to Amazon ECR
  ├─ Terraform Apply (Infrastructure)
  └─ Deploy to ECS/Fargate
      |
      v
AWS ECS Service Rolling Update
  ├─ New Tasks Start
  ├─ Health Checks Pass
  └─ Old Tasks Drain
```

---

## Prerequisites Checklist

### AWS Account Setup
- [ ] AWS Account created
- [ ] AWS CLI installed and configured
- [ ] IAM user with admin access (for initial setup)
- [ ] AWS credentials configured locally
- [ ] AWS region selected (e.g., `us-east-1`)

### GitHub Setup
- [ ] GitHub repository created
- [ ] GitHub Actions enabled
- [ ] Repository secrets configured (see below)

### Local Development
- [ ] Terraform installed (`terraform --version`)
- [ ] Docker installed and running
- [ ] Git configured

---

## Step-by-Step Setup Guide

### Phase 1: AWS Infrastructure Setup (Terraform)

#### Step 1.1: Create Terraform Directory Structure

```bash
mkdir -p terraform/{modules,environments/production}
cd terraform
```

#### Step 1.2: Initialize Terraform

```bash
cd terraform/environments/production
terraform init
```

#### Step 1.3: Apply Infrastructure

```bash
# Review plan
terraform plan

# Apply infrastructure
terraform apply
```

**This will create:**
- VPC with public/private subnets
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- ECR repository
- ECS cluster
- Application Load Balancer
- Security groups
- IAM roles
- S3 bucket

---

### Phase 2: GitHub Secrets Configuration

#### Step 2.1: Get AWS Credentials

```bash
# Create IAM user for CI/CD
aws iam create-user --user-name github-actions-cicd

# Create access key
aws iam create-access-key --user-name github-actions-cicd

# Attach policies (or create custom policy)
aws iam attach-user-policy --user-name github-actions-cicd \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

#### Step 2.2: Configure GitHub Secrets

Go to: **Repository Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ACCOUNT_ID` | AWS account ID | `123456789012` |
| `ECR_REPOSITORY` | ECR repository name | `expense-tracker-backend` |
| `ECS_CLUSTER` | ECS cluster name | `expense-tracker-cluster` |
| `ECS_SERVICE` | ECS service name | `expense-tracker-api` |
| `ECS_TASK_DEFINITION` | Task definition family | `expense-tracker-api` |
| `DATABASE_URL` | RDS connection string | `postgresql://user:pass@rds-endpoint:5432/db` |
| `REDIS_URL` | ElastiCache endpoint | `redis://elasticache-endpoint:6379/0` |
| `SECRET_KEY` | Application secret key | `your-32-char-secret-key` |
| `SENTRY_DSN` | Sentry DSN (optional) | `https://...@sentry.io/...` |

---

### Phase 3: Update CI/CD Workflows

#### Step 3.1: Update CI Workflow

The CI workflow (`.github/workflows/ci.yml`) will be updated to:
- Run linting, formatting, type checking
- Run tests with coverage
- Build Docker images
- Run security scans
- **Build Docker image** (for testing)

#### Step 3.2: Create CD Workflow

The CD workflow (`.github/workflows/cd.yml`) will:
- Build and tag Docker images
- Push to ECR
- Run Terraform apply
- Deploy to ECS/Fargate
- Verify deployment

---

### Phase 4: First Deployment

#### Step 4.1: Push Code to GitHub

```bash
git add .
git commit -m "Setup CI/CD pipeline"
git push origin main
```

#### Step 4.2: Monitor GitHub Actions

1. Go to **Actions** tab in GitHub
2. Watch CI workflow run
3. After merge to main, watch CD workflow

#### Step 4.3: Verify Deployment

```bash
# Get load balancer URL from Terraform output
terraform output -json | jq -r '.alb_dns_name.value'

# Test health endpoint
curl https://<alb-dns-name>.us-east-1.elb.amazonaws.com/health
```

---

## Infrastructure Components

### 1. Networking (VPC)
- VPC with CIDR `10.0.0.0/16`
- 2 Public subnets (for ALB)
- 2 Private subnets (for ECS tasks)
- Internet Gateway
- NAT Gateway (for private subnet internet access)

### 2. Compute (ECS/Fargate)
- ECS Cluster
- ECS Service with:
  - Desired count: 2
  - Minimum healthy: 1
  - Maximum percent: 200
  - Rolling update deployment
- Task Definition:
  - CPU: 1 vCPU
  - Memory: 2 GB
  - Health check: `/health`

### 3. Database (RDS)
- PostgreSQL 15
- Instance class: `db.t3.micro` (dev) or `db.t3.small` (prod)
- Multi-AZ: false (dev) or true (prod)
- Automated backups enabled

### 4. Cache (ElastiCache)
- Redis 7
- Node type: `cache.t3.micro` (dev) or `cache.t3.small` (prod)
- Cluster mode: disabled

### 5. Storage (S3)
- Bucket for receipts and reports
- Versioning enabled
- Lifecycle policies

### 6. Load Balancing
- Application Load Balancer
- Target group with health checks
- HTTPS listener (with ACM certificate)

### 7. Security
- Security groups for each component
- IAM roles with least privilege
- Secrets in AWS Secrets Manager (optional)

---

## Cost Estimation

### Monthly Costs (Approximate)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS Fargate | 2 tasks, 1 vCPU, 2GB | ~$30 |
| RDS PostgreSQL | db.t3.small | ~$30 |
| ElastiCache Redis | cache.t3.small | ~$15 |
| ALB | Standard | ~$20 |
| NAT Gateway | 1 instance | ~$35 |
| S3 | 10GB storage | ~$0.25 |
| Data Transfer | 100GB | ~$10 |
| **Total** | | **~$140/month** |

*Note: Costs vary by region and usage*

---

## Security Best Practices

1. ✅ **IAM Roles**: Use IAM roles, not access keys in containers
2. ✅ **Secrets Management**: Use AWS Secrets Manager or Parameter Store
3. ✅ **Network Isolation**: Private subnets for ECS tasks
4. ✅ **Security Groups**: Least privilege access
5. ✅ **Encryption**: Enable encryption at rest and in transit
6. ✅ **VPC**: Use private subnets for databases
7. ✅ **WAF**: Add AWS WAF for DDoS protection (optional)

---

## Monitoring & Alerts

### CloudWatch Metrics
- ECS service CPU/Memory utilization
- ALB request count and latency
- RDS connection count and CPU
- ElastiCache cache hit rate

### CloudWatch Alarms
- ECS service unhealthy tasks
- High CPU/Memory usage
- Database connection errors
- High error rate

### Logs
- ECS task logs → CloudWatch Logs
- Application logs → CloudWatch Logs
- ALB access logs → S3

---

## Rollback Procedure

### Quick Rollback

```bash
# 1. Get previous task definition revision
aws ecs describe-task-definition \
  --task-definition expense-tracker-api \
  --query 'taskDefinition.revision' \
  --output text

# 2. Update service to previous revision
aws ecs update-service \
  --cluster expense-tracker-cluster \
  --service expense-tracker-api \
  --task-definition expense-tracker-api:<previous-revision> \
  --force-new-deployment
```

### Terraform Rollback

```bash
cd terraform/environments/production
terraform state list
terraform apply -target=aws_ecs_service.api
```

---

## Troubleshooting

### Common Issues

1. **ECS Tasks Not Starting**
   - Check CloudWatch logs
   - Verify security groups
   - Check IAM role permissions
   - Verify environment variables

2. **Health Checks Failing**
   - Check application logs
   - Verify health endpoint responds
   - Check security group rules
   - Verify target group configuration

3. **Terraform Apply Fails**
   - Check AWS credentials
   - Verify resource limits
   - Check for naming conflicts
   - Review Terraform state

4. **Docker Build Fails**
   - Check Dockerfile syntax
   - Verify dependencies in pyproject.toml
   - Check GitHub Actions logs

---

## Next Steps

1. ✅ **Complete Phase 1**: Set up Terraform infrastructure
2. ✅ **Complete Phase 2**: Configure GitHub secrets
3. ✅ **Complete Phase 3**: Update CI/CD workflows
4. ✅ **Complete Phase 4**: First deployment
5. ✅ **Monitor**: Set up CloudWatch alarms
6. ✅ **Optimize**: Review costs and performance

---

## Support

- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **ECS Docs**: https://docs.aws.amazon.com/ecs/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**Last Updated**: 2026-01-08


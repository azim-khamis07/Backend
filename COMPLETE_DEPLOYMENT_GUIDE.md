# Complete CI/CD Deployment Guide

## 🎯 Overview

This guide provides a complete step-by-step plan to set up CI/CD pipeline for deploying the Expense Tracker Backend to AWS ECS/Fargate.

---

## 📋 Complete Setup Plan

### Phase 1: Prerequisites (15 minutes)

#### 1.1 Install Required Tools

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip && sudo mv terraform /usr/local/bin/

# Verify
aws --version
terraform version
```

#### 1.2 Configure AWS

```bash
# Configure AWS credentials
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region: us-east-1
# - Default output format: json

# Verify
aws sts get-caller-identity
# Note your Account ID
```

#### 1.3 Verify Prerequisites

```bash
# Run setup check
./scripts/setup_cicd.sh
```

---

### Phase 2: Terraform Infrastructure Setup (20 minutes)

#### 2.1 Configure Terraform Variables

```bash
cd terraform/environments/production

# Create configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**Required values in `terraform.tfvars`:**
```hcl
aws_region = "us-east-1"
project_name = "expense-tracker"

# Database - REQUIRED
db_password = "your-strong-password-here"

# Application - REQUIRED
secret_key = "your-32-character-secret-key-minimum"

# Optional: Adjust instance sizes
rds_instance_class = "db.t3.small"
redis_node_type = "cache.t3.small"
ecs_task_cpu = 1024
ecs_task_memory = 2048
```

#### 2.2 Initialize Terraform

```bash
# Initialize
terraform init

# Review plan
terraform plan

# Expected: Creates ~20 resources
# - VPC, Subnets, NAT Gateway
# - RDS PostgreSQL
# - ElastiCache Redis
# - ECR Repository
# - ECS Cluster & Service
# - Application Load Balancer
# - S3 Bucket
# - Security Groups
# - IAM Roles
```

#### 2.3 Create Infrastructure

```bash
# Apply (creates all AWS resources)
terraform apply
# Type: yes
# Wait ~15-20 minutes for all resources

# Save outputs
terraform output -json > outputs.json
```

#### 2.4 Get Important Values

```bash
# Get outputs
terraform output

# Key outputs:
# - alb_dns_name: Load balancer URL
# - rds_endpoint: Database endpoint
# - redis_endpoint: Redis endpoint
# - ecr_repository_url: ECR repository URL
```

---

### Phase 3: GitHub Secrets Configuration (10 minutes)

#### 3.1 Get AWS Account ID

```bash
aws sts get-caller-identity --query Account --output text
```

#### 3.2 Configure GitHub Secrets

Go to: **GitHub Repo → Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | From `aws configure` |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | From `aws configure` |
| `AWS_REGION` | `us-east-1` | Your AWS region |
| `AWS_ACCOUNT_ID` | Your account ID | `aws sts get-caller-identity` |
| `ECR_REPOSITORY` | `expense-tracker-backend` | From Terraform output |
| `ECS_CLUSTER` | `expense-tracker-cluster` | From Terraform output |
| `ECS_SERVICE` | `expense-tracker-api` | From Terraform output |
| `ECS_TASK_DEFINITION` | `expense-tracker-api` | From Terraform output |
| `SECRET_KEY` | Your secret key | From `terraform.tfvars` |
| `DATABASE_URL` | `postgresql://...` | From Terraform output + credentials |
| `REDIS_URL` | `redis://...` | From Terraform output |
| `CELERY_BROKER_URL` | `redis://...` | From Terraform output |
| `CELERY_RESULT_BACKEND` | `redis://...` | From Terraform output |

**Format for DATABASE_URL:**
```bash
# Get from Terraform
terraform output -raw rds_endpoint
# Format: postgresql://expenseuser:YOUR_PASSWORD@<endpoint>:5432/expensedb
```

**Format for Redis URLs:**
```bash
# Get from Terraform
terraform output -raw redis_endpoint
# Format: redis://<endpoint>:6379/0 (or /1, /2 for Celery)
```

---

### Phase 4: First Deployment (5 minutes)

#### 4.1 Push Code

```bash
# Commit all changes
git add .
git commit -m "Setup CI/CD pipeline with Terraform"
git push origin main
```

#### 4.2 Monitor Deployment

1. Go to **GitHub → Actions** tab
2. Watch CI workflow run (should pass)
3. After merge, watch CD workflow:
   - Build and push to ECR
   - Terraform apply (if needed)
   - Deploy to ECS
   - Verify deployment

#### 4.3 Verify Deployment

```bash
# Get ALB DNS
terraform output -raw alb_dns_name

# Test health endpoint
curl http://$(terraform output -raw alb_dns_name)/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Expense Tracker API",
#   "version": "1.0.0",
#   "redis": "connected",
#   "database": "connected"
# }
```

---

## 🔄 CI/CD Pipeline Flow

### On Push/PR (CI)

```
Push/PR → GitHub Actions
  ├─ Lint & Format Check
  ├─ Type Checking
  ├─ Unit & Integration Tests
  ├─ Security Scan
  └─ Docker Image Build (test)
```

### On Merge to Main (CD)

```
Merge to Main → GitHub Actions
  ├─ Build Docker Image
  ├─ Tag with Commit SHA
  ├─ Push to ECR
  ├─ Terraform Apply (if infrastructure changes)
  ├─ Deploy to ECS
  ├─ Rolling Update
  └─ Health Check Verification
```

---

## 📁 File Structure

```
.
├── .github/workflows/
│   ├── ci.yml          # CI workflow (lint, test, build)
│   └── cd.yml          # CD workflow (deploy to AWS)
├── terraform/
│   ├── modules/
│   │   ├── vpc/        # VPC, subnets, NAT
│   │   ├── rds/        # PostgreSQL database
│   │   ├── elasticache/# Redis cache
│   │   ├── ecr/        # Docker registry
│   │   ├── ecs/        # ECS cluster & service
│   │   ├── alb/        # Load balancer
│   │   └── s3/         # Object storage
│   └── environments/production/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars.example
└── scripts/
    └── setup_cicd.sh   # Setup verification script
```

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Terraform
cd terraform/environments/production
terraform init
terraform plan
terraform apply
terraform output

# AWS ECS
aws ecs describe-services --cluster expense-tracker-cluster --services expense-tracker-api
aws ecs update-service --cluster expense-tracker-cluster --service expense-tracker-api --force-new-deployment

# View logs
aws logs tail /ecs/expense-tracker-api --follow

# Scale service
aws ecs update-service --cluster expense-tracker-cluster --service expense-tracker-api --desired-count 4
```

### Important URLs

- **GitHub Actions**: `https://github.com/<user>/<repo>/actions`
- **AWS Console**: `https://console.aws.amazon.com`
- **ECS Cluster**: `https://console.aws.amazon.com/ecs/v2/clusters/expense-tracker-cluster`
- **API Health**: `http://<alb-dns-name>/health`
- **API Docs**: `http://<alb-dns-name>/docs`

---

## 🚨 Troubleshooting

### Terraform Apply Fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check for resource limits
# Some AWS accounts have default limits

# Review error message
terraform apply 2>&1 | tee apply.log
```

### ECS Tasks Not Starting

```bash
# Check task status
aws ecs describe-tasks --cluster expense-tracker-cluster --tasks <task-id>

# Check logs
aws logs tail /ecs/expense-tracker-api --follow

# Common issues:
# - Environment variables missing
# - Security group rules
# - IAM permissions
```

### GitHub Actions Fails

```bash
# Check workflow logs in GitHub
# Common issues:
# - Missing secrets
# - ECR permissions
# - Terraform state locked
```

---

## 📊 Cost Monitoring

### Estimated Monthly Costs

- ECS Fargate: ~$30 (2 tasks)
- RDS PostgreSQL: ~$30
- ElastiCache Redis: ~$15
- ALB: ~$20
- NAT Gateway: ~$35
- Data Transfer: ~$10
- **Total: ~$140/month**

### Cost Optimization

- Use smaller instance types for dev
- Enable RDS Multi-AZ only for production
- Use NAT Gateway only if needed
- Monitor and scale down when possible

---

## ✅ Success Criteria

After completing this guide, you should have:

- ✅ CI pipeline running on every PR
- ✅ CD pipeline deploying on merge to main
- ✅ Application running on AWS ECS/Fargate
- ✅ Database and Redis configured
- ✅ Load balancer with health checks
- ✅ Rolling updates working
- ✅ Monitoring and logging enabled

---

## 📚 Additional Resources

- **CICD_SETUP_PLAN.md** - Detailed setup plan
- **CICD_QUICK_START.md** - Quick reference
- **DEPLOYMENT_PLAN.md** - Deployment details
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist

---

**Last Updated**: 2026-01-08


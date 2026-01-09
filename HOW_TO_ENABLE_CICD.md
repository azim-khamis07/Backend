# How to Enable CI/CD Pipeline - Step-by-Step Guide

**Last Updated**: 2026-01-08  
**Status**: Ready to Enable

---

## 🎯 Overview

Your CI/CD workflows are **already created** in `.github/workflows/`! You just need to:
1. ✅ Configure GitHub Secrets
2. ✅ Enable GitHub Actions (if not already enabled)
3. ✅ Test the pipeline

---

## ✅ What You Already Have

### CI Workflow (`.github/workflows/ci.yml`)
- ✅ Runs on every push/PR
- ✅ Lint & format checks
- ✅ Type checking (mypy)
- ✅ Unit & integration tests
- ✅ Security scans (bandit, safety)
- ✅ Docker image build test

### CD Workflow (`.github/workflows/cd.yml`)
- ✅ Auto-deploys on push to `main` → **production**
- ✅ Auto-deploys on push to `develop` → **dev**
- ✅ Manual deployments via workflow dispatch
- ✅ Builds and pushes to ECR
- ✅ Deploys to ECS Fargate
- ✅ Rolling updates with health checks

---

## 📋 Step-by-Step Setup

### Step 1: Get Required Values (5 minutes)

First, let's get all the values you need:

```bash
cd /home/azim/python-projects/Backend

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"

# Get AWS credentials (if you have them in ~/.aws/credentials)
# If not, you'll need to create an IAM user for GitHub Actions

# Get values from dev environment (already deployed)
cd terraform/environments/dev
terraform output -json | jq -r '
  "ECR_REPOSITORY_DEV: expense-tracker-backend-dev",
  "ECS_CLUSTER_DEV: expense-tracker-cluster-dev",
  "ECS_SERVICE_DEV: expense-tracker-api-dev",
  "RDS_ENDPOINT: " + (.rds_endpoint.value // "not-set"),
  "REDIS_ENDPOINT: " + (.redis_endpoint.value // "not-set")
'
```

---

### Step 2: Create IAM User for GitHub Actions (10 minutes)

**Why?** GitHub Actions needs AWS credentials to deploy to ECR and ECS.

```bash
# Create IAM user
aws iam create-user --user-name github-actions-expense-tracker

# Create access key
aws iam create-access-key --user-name github-actions-expense-tracker

# Save the output! You'll need:
# - AccessKeyId
# - SecretAccessKey

# Attach policies (or create custom policy with minimal permissions)
aws iam attach-user-policy \
  --user-name github-actions-expense-tracker \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Optional: Create custom policy with minimal permissions (more secure)
# See below for policy example
```

**Minimal IAM Policy** (recommended for production):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:*",
        "ecs:*",
        "logs:*",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "iam:PassRole",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeLoadBalancers"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Step 3: Configure GitHub Secrets (10 minutes)

Go to your GitHub repository and add secrets:

**Path**: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

#### 3.1: Add Repository Secrets

Click **"New repository secret"** and add each one:

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `AWS_ACCESS_KEY_ID` | From Step 2 | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | From Step 2 | IAM user secret key |
| `AWS_REGION` | `us-east-1` | Your AWS region |
| `AWS_ACCOUNT_ID` | From Step 1 | `aws sts get-caller-identity` |

**Example:**
```
Name: AWS_ACCESS_KEY_ID
Value: AKIAIOSFODNN7EXAMPLE
```

#### 3.2: Get Connection Strings

```bash
cd terraform/environments/dev

# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -json | jq -r '.rds_endpoint.value')
echo "RDS Endpoint: $RDS_ENDPOINT"

# Get Redis endpoint
REDIS_ENDPOINT=$(terraform output -json | jq -r '.redis_endpoint.value')
echo "Redis Endpoint: $REDIS_ENDPOINT"

# Get database password from terraform.tfvars (you set this earlier)
# Read from terraform.tfvars (manually or with care)
```

**Format Database URL:**
```
postgresql://expenseuser:YOUR_PASSWORD@expense-tracker-rds-dev-db.covoyosga5xa.us-east-1.rds.amazonaws.com:5432/expensedb_dev
```

**Format Redis URLs:**
```
redis://expense-tracker-redis-dev-redis.wlzlxg.ng.0001.use1.cache.amazonaws.com:6379/0
redis://expense-tracker-redis-dev-redis.wlzlxg.ng.0001.use1.cache.amazonaws.com:6379/1
redis://expense-tracker-redis-dev-redis.wlzlxg.ng.0001.use1.cache.amazonaws.com:6379/2
```

#### 3.3: Add Application Secrets (Optional)

These are only needed if your application reads them from environment variables:

| Secret Name | Value | Example |
|------------|-------|---------|
| `SECRET_KEY` | Your app secret key | `your-32-char-secret-key-here` |
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://host:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://host:6379/2` |

**Note**: The CD workflow doesn't require these secrets directly - ECS task definition uses Terraform outputs. But if your application needs them at build time, add them here.

---

### Step 4: Enable GitHub Actions (2 minutes)

1. Go to: **GitHub Repo → Settings → Actions → General**
2. Under **"Workflow permissions"**, select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests** (optional)
3. Click **"Save"**

---

### Step 5: Test CI Pipeline (5 minutes)

#### 5.1: Create a Test Branch

```bash
cd /home/azim/python-projects/Backend

# Create test branch
git checkout -b test-ci-pipeline

# Make a small change
echo "# CI/CD Test" >> test-ci.md

# Commit and push
git add test-ci.md
git commit -m "Test CI pipeline"
git push origin test-ci-pipeline
```

#### 5.2: Monitor CI Run

1. Go to: **GitHub Repo → Actions tab**
2. You should see a workflow run called **"CI"**
3. Click on it to see progress
4. Check that all jobs pass:
   - ✅ Lint & Format
   - ✅ Type Check
   - ✅ Test
   - ✅ Security Scan
   - ✅ Build Docker

#### 5.3: Create Pull Request (Optional)

```bash
# Create PR from test branch
# GitHub will automatically run CI on the PR
```

---

### Step 6: Test CD Pipeline (10 minutes)

#### Option A: Deploy to Dev (Automatic)

The CD workflow automatically deploys to `dev` when you push to `develop` branch:

```bash
# Create/switch to develop branch
git checkout -b develop
# or: git checkout develop

# Make a change
echo "# Deploy to dev" >> deploy-test.md

# Commit and push
git add deploy-test.md
git commit -m "Test deployment to dev"
git push origin develop

# Monitor: GitHub → Actions → CD workflow
```

#### Option B: Manual Deployment (Recommended for First Test)

1. Go to: **GitHub Repo → Actions → CD → Run workflow**
2. Select:
   - **Environment**: `dev`
   - **Branch**: `main` (or your current branch)
3. Click **"Run workflow"**

#### 6.2: Monitor CD Run

Watch the deployment:
1. **determine-environment**: Determines target environment
2. **build-and-push**: Builds Docker image, pushes to ECR
3. **deploy-infrastructure**: (Only if `[terraform]` in commit message)
4. **deploy-ecs**: Deploys to ECS Fargate
5. **verify-deployment**: Checks health endpoint

---

### Step 7: Verify Deployment (5 minutes)

After CD workflow completes:

```bash
# Get ALB DNS
cd terraform/environments/dev
ALB_DNS=$(terraform output -raw alb_dns_name)
echo "API URL: http://$ALB_DNS"

# Test health endpoint
curl http://$ALB_DNS/health

# Check ECS service status
aws ecs describe-services \
  --cluster expense-tracker-cluster-dev \
  --services expense-tracker-api-dev \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Events:events[0:3]}'

# View logs
aws logs tail /ecs/expense-tracker-api-dev --follow --region us-east-1
```

---

## 🔄 How It Works

### CI Pipeline Flow

```
Push/PR → GitHub Actions CI
  ├─ Lint & Format Check
  ├─ Type Check (mypy)
  ├─ Run Tests (pytest)
  ├─ Security Scan (bandit, safety)
  └─ Build Docker Image (test)
```

**Triggers**:
- ✅ On every push to `main` or `develop`
- ✅ On every pull request to `main` or `develop`

### CD Pipeline Flow

```
Push to main/develop → GitHub Actions CD
  ├─ Determine Environment
  │   ├─ main → production
  │   ├─ develop → dev
  │   └─ workflow_dispatch → manual selection
  ├─ Build & Push to ECR
  │   ├─ Build Docker image
  │   ├─ Tag with commit SHA
  │   └─ Push to ECR repository
  ├─ Deploy Infrastructure (optional)
  │   └─ Only if [terraform] in commit message
  ├─ Deploy to ECS
  │   ├─ Update task definition
  │   ├─ Deploy new image
  │   └─ Rolling update
  └─ Verify Deployment
      └─ Health check
```

**Triggers**:
- ✅ Push to `main` → deploys to **production**
- ✅ Push to `develop` → deploys to **dev**
- ✅ Manual via workflow dispatch → any environment

---

## 📝 Quick Reference

### Manual Deployment

**Via GitHub UI**:
1. Go to: **Actions → CD → Run workflow**
2. Select environment
3. Click **"Run workflow"**

**Via Command** (after setup):
```bash
git push origin main  # Auto-deploys to production
```

### Infrastructure Changes

To update infrastructure via CI/CD, include `[terraform]` in commit message:

```bash
git commit -m "[terraform] Update RDS instance size"
git push origin main
```

This triggers the `deploy-infrastructure` job in the CD workflow.

### Branch Strategy

| Branch | CI Runs? | CD Deploys To | When |
|--------|----------|---------------|------|
| `feature/*` | ✅ Yes | ❌ No | On push/PR |
| `develop` | ✅ Yes | ✅ Dev | On push |
| `main` | ✅ Yes | ✅ Production | On push |

---

## 🔧 Troubleshooting

### CI Fails

**Issue**: Tests failing
```bash
# Run tests locally first
pytest

# Fix issues, then push
git push origin your-branch
```

**Issue**: Linting errors
```bash
# Run linters locally
black app/ tests/
isort app/ tests/
flake8 app/ tests/

# Fix, commit, push
```

### CD Fails

**Issue**: "Access Denied" errors
- ✅ Check GitHub Secrets are correct
- ✅ Verify IAM user has necessary permissions
- ✅ Check AWS credentials in secrets

**Issue**: "ECR repository not found"
- ✅ Verify repository exists: `aws ecr describe-repositories`
- ✅ Check repository name in secrets matches Terraform output

**Issue**: "ECS service not found"
- ✅ Verify service exists: `aws ecs describe-services --cluster <cluster> --services <service>`
- ✅ Check cluster/service names match Terraform outputs

**Issue**: "Task definition not found"
- ✅ The task definition is created by Terraform
- ✅ Make sure infrastructure is deployed first
- ✅ Check task definition family name matches

### View Workflow Logs

1. Go to: **GitHub → Actions**
2. Click on the workflow run
3. Click on the failed job
4. Expand the failed step to see error details

---

## ✅ Checklist

Use this checklist to ensure everything is set up:

### Prerequisites
- [ ] GitHub repository created
- [ ] GitHub Actions enabled
- [ ] AWS account ready
- [ ] Terraform infrastructure deployed (dev environment is done ✅)

### AWS Setup
- [ ] IAM user created for GitHub Actions
- [ ] Access key and secret key saved
- [ ] IAM permissions configured
- [ ] ECR repository exists (from Terraform)
- [ ] ECS cluster exists (from Terraform)

### GitHub Secrets
- [ ] `AWS_ACCESS_KEY_ID` added
- [ ] `AWS_SECRET_ACCESS_KEY` added
- [ ] `AWS_REGION` added
- [ ] `AWS_ACCOUNT_ID` added
- [ ] Optional: `SECRET_KEY` (if needed)
- [ ] Optional: `DATABASE_URL` (if needed)
- [ ] Optional: `REDIS_URL` (if needed)

### Testing
- [ ] CI workflow runs successfully
- [ ] CD workflow can build and push to ECR
- [ ] CD workflow can deploy to ECS
- [ ] Health check passes after deployment

---

## 🚀 Quick Setup Script

I'll create a script to help you get started:

```bash
# Run the setup script
./scripts/setup_cicd.sh

# This will:
# 1. Check prerequisites
# 2. Show you what secrets to add
# 3. Provide values from Terraform outputs
```

---

## 📚 Additional Resources

- **Full Setup Guide**: `CICD_SETUP_PLAN.md`
- **Quick Start**: `CICD_QUICK_START.md`
- **Deployment Guide**: `COMPLETE_DEPLOYMENT_GUIDE.md`
- **Multi-Environment**: `MULTI_ENVIRONMENT_DEPLOYMENT.md`

---

## 🎯 Summary

Your CI/CD pipeline is **ready to use**! Just:

1. ✅ **Add GitHub Secrets** (10 minutes)
2. ✅ **Enable GitHub Actions** (2 minutes)
3. ✅ **Push to test** (5 minutes)

Once configured, every push to `main` will automatically deploy to production! 🚀

---

**Need help?** Check the troubleshooting section or review the workflow logs in GitHub Actions.


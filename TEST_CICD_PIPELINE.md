# Testing CI/CD Pipeline - Guide

**Status**: GitHub Secrets Added ✅  
**Next**: Test the Pipeline

---

## ✅ Setup Complete!

You've successfully:
- ✅ Created IAM user for GitHub Actions
- ✅ Added GitHub Secrets
- ✅ Infrastructure deployed (dev environment)

---

## 🧪 Testing the CI/CD Pipeline

### Option 1: Test CI Pipeline (Recommended First)

This tests code quality without deploying:

```bash
cd /home/azim/python-projects/Backend

# Create a test branch
git checkout -b test-ci-pipeline

# Make a small change
echo "# CI/CD Test - $(date)" >> test-cicd.md

# Commit and push
git add test-cicd.md
git commit -m "Test CI pipeline"
git push origin test-ci-pipeline

# Monitor: GitHub → Actions → CI workflow
```

**What to Expect:**
- ✅ Lint & Format job runs
- ✅ Type Check job runs
- ✅ Test job runs (with PostgreSQL & Redis)
- ✅ Security Scan job runs
- ✅ Build Docker job runs

**All jobs should pass** ✅

---

### Option 2: Test CD Pipeline (Deploy to Dev)

This actually deploys to your dev environment:

#### Option A: Automatic Deploy (Push to develop)

```bash
# Switch to develop branch (or create if doesn't exist)
git checkout -b develop  # if doesn't exist
# OR
git checkout develop     # if already exists

# Make a small change
echo "# Deploy to dev - $(date)" >> deploy-test.md

# Commit and push
git add deploy-test.md
git commit -m "Test CD pipeline - deploy to dev"
git push origin develop

# Monitor: GitHub → Actions → CD workflow
```

**What to Expect:**
1. ✅ `determine-environment` → Detects `dev`
2. ✅ `build-and-push` → Builds Docker image, pushes to ECR
3. ✅ `deploy-ecs` → Deploys to ECS Fargate
4. ✅ `verify-deployment` → Health check

**Note**: ECS service will try to deploy but may fail if Docker image doesn't exist in ECR yet. That's normal for first deployment - you'll need to push an image first.

#### Option B: Manual Deploy (Workflow Dispatch)

1. Go to: **GitHub Repo → Actions → CD → Run workflow**
2. Select:
   - **Environment**: `dev`
   - **Branch**: `main` (or current branch)
3. Click **"Run workflow"**
4. Monitor the deployment

---

## 📊 What to Monitor

### GitHub Actions Dashboard

Go to: **GitHub Repo → Actions tab**

You'll see:
- **CI workflow**: Runs on every push/PR
- **CD workflow**: Runs on push to `main`/`develop` or manual dispatch

### Workflow Run Details

Click on any workflow run to see:
- ✅ Job status (green = success, red = failed)
- 📋 Step-by-step logs
- ⏱️ Execution time
- 🔍 Error details (if any)

---

## 🎯 Expected Results

### CI Pipeline (Should Pass)

All jobs should complete successfully:
- ✅ Lint & Format: `PASSED`
- ✅ Type Check: `PASSED`
- ✅ Test: `PASSED` (tests run with coverage)
- ✅ Security Scan: `PASSED`
- ✅ Build Docker: `PASSED`

### CD Pipeline (First Time)

On first deployment, expect:
1. ✅ `build-and-push`: **SUCCESS** (builds and pushes to ECR)
2. ⚠️ `deploy-ecs`: **MAY FAIL** (if task definition doesn't exist or image issues)
   - This is normal - you'll need to ensure:
     - Docker image builds successfully
     - Image is pushed to ECR
     - ECS task definition exists (created by Terraform ✅)

---

## 🔧 Troubleshooting First Deployment

### Issue: "Task definition not found"

**Solution**: Task definition is created by Terraform. If missing, update ECS module or check Terraform state.

### Issue: "Image not found in ECR"

**Solution**: 
1. The CD workflow will build and push the image automatically ✅
2. But first, make sure your Dockerfile is correct
3. Check ECR repository exists: `aws ecr describe-repositories`

### Issue: "ECS service failed to start"

**Solution**:
- Check CloudWatch logs: `aws logs tail /ecs/expense-tracker-api-dev --follow`
- Check task definition: `aws ecs describe-task-definition --task-definition expense-tracker-api-dev`
- Verify environment variables in task definition

---

## ✅ Success Indicators

### CI Pipeline Success

All checks pass:
```
✅ Lint & Format (2m 30s)
✅ Type Check (1m 15s)
✅ Test (5m 20s)
✅ Security Scan (2m 10s)
✅ Build Docker (3m 45s)
```

### CD Pipeline Success

```
✅ determine-environment (30s)
✅ build-and-push (5m 15s)
✅ deploy-ecs (2m 30s)
✅ verify-deployment (1m 00s)
```

**Deployment successful!** 🎉

---

## 🚀 After First Successful Deployment

### 1. Verify API is Accessible

```bash
# Get ALB DNS
cd terraform/environments/dev
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health endpoint
curl http://$ALB_DNS/health

# Should return:
# {"status":"healthy","service":"Expense Tracker API",...}
```

### 2. View Application Logs

```bash
aws logs tail /ecs/expense-tracker-api-dev --follow --region us-east-1
```

### 3. Check ECS Service Status

```bash
aws ecs describe-services \
  --cluster expense-tracker-cluster-dev \
  --services expense-tracker-api-dev \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Events:events[0:3]}'
```

---

## 📝 Next Steps After Testing

### 1. Set Up Production Environment

```bash
cd terraform/environments/production
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform plan
terraform apply
```

### 2. Configure Production Secrets

Add production-specific secrets to GitHub Environments:
- Go to: **Settings → Environments → New environment**
- Create: `production`
- Add production-specific secrets

### 3. Set Up Branch Protection (Recommended)

1. Go to: **Settings → Branches → Add branch protection rule**
2. Select branch: `main`
3. Enable:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date

---

## 🎉 You're All Set!

Once testing is complete:

- ✅ **CI** runs automatically on every push/PR
- ✅ **CD** deploys automatically on merge to `main`
- ✅ Manual deployments available via workflow dispatch
- ✅ Rolling updates with health checks
- ✅ Automatic rollback on failure

---

## 📚 Additional Resources

- **Troubleshooting**: Check workflow logs in GitHub Actions
- **Monitoring**: CloudWatch logs and metrics
- **Full Guide**: `HOW_TO_ENABLE_CICD.md`
- **Quick Reference**: `CICD_QUICK_START.md`

---

**Ready to test?** Push a commit and watch the magic happen! 🚀


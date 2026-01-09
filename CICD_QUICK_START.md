# CI/CD Quick Start Guide

## 🚀 Get Your Deployment Environment Ready in 30 Minutes

### Step 1: Prerequisites (5 min)

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip && sudo mv terraform /usr/local/bin/

# Configure AWS
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Output (json)

# Verify
aws sts get-caller-identity
terraform version
```

### Step 2: Set Up Terraform (10 min)

```bash
cd terraform/environments/production

# Create configuration file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
# Required: db_password, secret_key

# Initialize
terraform init

# Review what will be created
terraform plan
```

### Step 3: Create AWS Infrastructure (10 min)

```bash
# Apply Terraform (creates all AWS resources)
terraform apply
# Type: yes

# This creates:
# - VPC, Subnets, NAT Gateway
# - RDS PostgreSQL
# - ElastiCache Redis  
# - ECR Repository
# - ECS Cluster & Service
# - Application Load Balancer
# - S3 Bucket
# - Security Groups
# - IAM Roles

# Get important outputs
terraform output -json > outputs.json
```

### Step 4: Configure GitHub Secrets (5 min)

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets (get values from Terraform outputs):

```
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=<from: aws sts get-caller-identity>
ECR_REPOSITORY=expense-tracker-backend
ECS_CLUSTER=expense-tracker-cluster
ECS_SERVICE=expense-tracker-api
ECS_TASK_DEFINITION=expense-tracker-api
SECRET_KEY=<from terraform.tfvars>
DATABASE_URL=<from terraform output rds_endpoint>
REDIS_URL=<from terraform output redis_endpoint>
```

### Step 5: First Deployment (Automatic)

```bash
# Push to main branch
git add .
git commit -m "Setup CI/CD pipeline"
git push origin main

# Monitor deployment
# Go to: GitHub → Actions tab
```

### Step 6: Verify Deployment

```bash
# Get ALB DNS from Terraform
terraform output alb_dns_name

# Test health endpoint
curl http://$(terraform output -raw alb_dns_name)/health

# Should return:
# {"status":"healthy","service":"Expense Tracker API",...}
```

## ✅ Done!

Your application is now:
- ✅ Automatically tested on every PR
- ✅ Automatically deployed on merge to main
- ✅ Running on AWS ECS/Fargate
- ✅ Behind a load balancer
- ✅ With rolling updates and health checks

## 📋 What Happens Next

### On Every Push/PR:
1. ✅ Lint & format check
2. ✅ Type checking
3. ✅ Unit & integration tests
4. ✅ Security scan
5. ✅ Docker image build

### On Merge to Main:
1. ✅ Build Docker image
2. ✅ Tag with commit SHA
3. ✅ Push to ECR
4. ✅ Run Terraform (if needed)
5. ✅ Deploy to ECS
6. ✅ Rolling update
7. ✅ Health check verification

## 🔧 Useful Commands

```bash
# View ECS service status
aws ecs describe-services \
  --cluster expense-tracker-cluster \
  --services expense-tracker-api

# View ECS logs
aws logs tail /ecs/expense-tracker-api --follow

# Scale ECS service
aws ecs update-service \
  --cluster expense-tracker-cluster \
  --service expense-tracker-api \
  --desired-count 4

# View Terraform state
cd terraform/environments/production
terraform state list
terraform show
```

## 📚 Full Documentation

- `CICD_SETUP_PLAN.md` - Complete setup guide
- `QUICK_CICD_SETUP.md` - Quick reference
- `DEPLOYMENT_PLAN.md` - Deployment details


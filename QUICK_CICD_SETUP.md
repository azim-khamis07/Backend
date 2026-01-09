# Quick CI/CD Setup Guide

## 🚀 Fastest Path to Production

### Prerequisites (5 minutes)

```bash
# 1. Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 2. Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# 3. Configure AWS
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format

# 4. Verify
./scripts/setup_cicd.sh
```

### Step 1: Configure GitHub Secrets (10 minutes)

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
ECR_REPOSITORY=expense-tracker-backend
ECS_CLUSTER=expense-tracker-cluster
ECS_SERVICE=expense-tracker-api
ECS_TASK_DEFINITION=expense-tracker-api
SECRET_KEY=your-32-char-secret-key
DATABASE_URL=postgresql://... (will be set after Terraform)
REDIS_URL=redis://... (will be set after Terraform)
```

### Step 2: Set Up Terraform (15 minutes)

```bash
cd terraform/environments/production

# Create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
nano terraform.tfvars

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates all AWS resources)
terraform apply
```

**This creates:**
- VPC, Subnets, NAT Gateway
- RDS PostgreSQL
- ElastiCache Redis
- ECR Repository
- ECS Cluster & Service
- Application Load Balancer
- S3 Bucket
- Security Groups
- IAM Roles

### Step 3: Update GitHub Secrets with Terraform Outputs

```bash
# Get outputs
terraform output -json

# Update GitHub secrets with:
# - DATABASE_URL (from RDS endpoint)
# - REDIS_URL (from ElastiCache endpoint)
```

### Step 4: First Deployment (5 minutes)

```bash
# Push to main branch
git add .
git commit -m "Setup CI/CD pipeline"
git push origin main

# Monitor deployment
# Go to: GitHub → Actions tab
```

### Step 5: Verify Deployment

```bash
# Get ALB DNS from Terraform
terraform output alb_dns_name

# Test health endpoint
curl https://<alb-dns-name>/health
```

## 🎉 Done!

Your application is now:
- ✅ Automatically tested on every PR
- ✅ Automatically deployed on merge to main
- ✅ Running on AWS ECS/Fargate
- ✅ Behind a load balancer
- ✅ With rolling updates

## 📋 What Happens on Each Push

### On PR/Push to any branch:
1. Lint & format check
2. Type checking
3. Unit & integration tests
4. Security scan
5. Docker image build (test)

### On merge to main:
1. Build Docker image
2. Tag with commit SHA
3. Push to ECR
4. Run Terraform (if infrastructure changes)
5. Deploy to ECS
6. Rolling update
7. Health check verification

## 🔧 Common Commands

```bash
# View Terraform state
cd terraform/environments/production
terraform state list

# Update ECS service manually
aws ecs update-service \
  --cluster expense-tracker-cluster \
  --service expense-tracker-api \
  --force-new-deployment

# View ECS logs
aws logs tail /ecs/expense-tracker-api --follow

# Scale ECS service
aws ecs update-service \
  --cluster expense-tracker-cluster \
  --service expense-tracker-api \
  --desired-count 4
```

## 📚 Full Documentation

For detailed setup instructions, see:
- `CICD_SETUP_PLAN.md` - Complete setup guide
- `DEPLOYMENT_PLAN.md` - Deployment details
- `terraform/` - Infrastructure as code


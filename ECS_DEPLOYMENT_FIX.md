# ECS Service Deployment Fix

## 🚨 Problem

ECS service fails to reach stable state with error:
```
Error: Resource is not in the state servicesStable
```

## 🔍 Root Causes Identified

1. **Missing `curl` in container** - Health check uses `curl` but it's not installed
2. **Hardcoded ENVIRONMENT** - Set to "production" for all environments
3. **Health check too strict** - Not enough time for app startup

## ✅ Fixes Applied

### 1. Added curl to Dockerfile

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \  # Added for health checks
    && rm -rf /var/lib/apt/lists/*
```

### 2. Made ENVIRONMENT Variable Dynamic

**terraform/modules/ecs/variables.tf:**
```hcl
variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}
```

**terraform/modules/ecs/main.tf:**
```hcl
environment = [
  {
    name  = "ENVIRONMENT"
    value = var.environment  # Now dynamic
  },
  ...
]
```

**terraform/environments/dev/main.tf:**
```hcl
module "ecs" {
  ...
  environment = "development"  # Set for dev environment
  ...
}
```

### 3. Increased Health Check Grace Periods

**terraform/modules/ecs/main.tf:**
```hcl
healthCheck = {
  command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval    = 30
  timeout     = 10      # Increased from 5
  retries     = 3
  startPeriod = 120     # Increased from 60
}

health_check_grace_period_seconds = 120  # Increased from 60
```

## 🚀 Deployment Steps

### Step 1: Rebuild Docker Image

The Dockerfile change requires rebuilding:

```bash
# Build locally (optional - CI/CD will do this)
docker build -t expense-tracker-backend:latest -f docker/Dockerfile .

# Or let CI/CD rebuild on next push
```

### Step 2: Update Terraform

Apply Terraform changes:

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### Step 3: Retry Deployment

After applying changes:
1. Wait for Terraform to update the task definition
2. Retry the GitHub Actions workflow
3. Or push a new commit to trigger deployment

## 🔍 Troubleshooting

### Check CloudWatch Logs

```bash
aws logs tail /ecs/expense-tracker-api-dev --follow --region us-east-1
```

### Check ECS Service Status

```bash
aws ecs describe-services \
  --cluster expense-tracker-cluster-dev \
  --services expense-tracker-api-dev \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Events:events[0:3]}'
```

### Check Task Status

```bash
aws ecs list-tasks \
  --cluster expense-tracker-cluster-dev \
  --service-name expense-tracker-api-dev \
  --region us-east-1

# Get task details
aws ecs describe-tasks \
  --cluster expense-tracker-cluster-dev \
  --tasks <task-id> \
  --region us-east-1 \
  --query 'tasks[0].{LastStatus:lastStatus,HealthStatus:healthStatus,StoppedReason:stoppedReason}'
```

### Common Issues

1. **Database connection fails**
   - Check RDS security group allows ECS security group
   - Verify DATABASE_URL is correct
   - Check RDS is accessible from private subnets

2. **Redis connection fails**
   - Check ElastiCache security group allows ECS security group
   - Verify REDIS_URL is correct
   - Check ElastiCache is accessible from private subnets

3. **Health check fails**
   - Check if app is starting correctly (logs)
   - Verify /health endpoint returns 200
   - Check if curl is available (should be fixed now)

4. **Container crashes**
   - Check CloudWatch logs for errors
   - Verify all environment variables are set
   - Check if app dependencies are installed

## 📋 Expected Behavior

After fixes:
1. ✅ Container starts successfully
2. ✅ Health check passes after 120 seconds
3. ✅ Service reaches stable state
4. ✅ Tasks remain running

## 🎯 Next Steps

1. Commit and push these changes
2. CI/CD will rebuild Docker image with curl
3. Apply Terraform changes
4. Retry deployment
5. Monitor CloudWatch logs for any remaining issues


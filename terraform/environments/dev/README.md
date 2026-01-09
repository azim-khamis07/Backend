# Development Environment

This directory contains Terraform configuration for the **development** environment.

## Quick Start

```bash
# 1. Configure variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with dev values

# 2. Initialize
terraform init

# 3. Review plan
terraform plan

# 4. Apply
terraform apply
```

## Environment Characteristics

- **Cost-optimized**: Smaller instances
- **Single instance**: 1 ECS task
- **No NAT Gateway**: Cost savings
- **Small database**: db.t3.micro
- **VPC CIDR**: 10.1.0.0/16

## Resources Created

- VPC with public/private subnets (no NAT)
- RDS PostgreSQL (db.t3.micro)
- ElastiCache Redis (cache.t3.micro)
- ECR repository
- ECS cluster & service (1 task, 0.5 vCPU, 1GB)
- Application Load Balancer
- S3 bucket

## Monthly Cost

Approximately **~$51/month**

## Deployment

- **Automatic**: On push to `develop` branch
- **Manual**: Via GitHub Actions workflow dispatch

## Outputs

```bash
terraform output
```

Key outputs:
- `alb_dns_name`: Load balancer URL
- `rds_endpoint`: Database endpoint
- `redis_endpoint`: Redis endpoint


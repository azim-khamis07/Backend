# Staging Environment

This directory contains Terraform configuration for the **staging** environment.

## Quick Start

```bash
# 1. Configure variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with staging values

# 2. Initialize
terraform init

# 3. Review plan
terraform plan

# 4. Apply
terraform apply
```

## Environment Characteristics

- **Production-like**: Similar to production setup
- **Multiple instances**: 2 ECS tasks
- **Full networking**: NAT Gateway enabled
- **Medium database**: db.t3.small
- **VPC CIDR**: 10.2.0.0/16

## Resources Created

- VPC with public/private subnets (with NAT)
- RDS PostgreSQL (db.t3.small)
- ElastiCache Redis (cache.t3.small)
- ECR repository
- ECS cluster & service (2 tasks, 1 vCPU, 2GB)
- Application Load Balancer
- S3 bucket

## Monthly Cost

Approximately **~$130/month**

## Deployment

- **Automatic**: On push to `develop` branch (optional)
- **Manual**: Via GitHub Actions workflow dispatch

## Outputs

```bash
terraform output
```

Key outputs:
- `alb_dns_name`: Load balancer URL
- `rds_endpoint`: Database endpoint
- `redis_endpoint`: Redis endpoint


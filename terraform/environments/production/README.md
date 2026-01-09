# Terraform Production Environment

This directory contains Terraform configuration for the production environment.

## Quick Start

### 1. Configure Variables

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

## Required Variables

- `db_password`: Database master password
- `secret_key`: Application secret key (min 32 chars)

## Outputs

After applying, get important values:

```bash
# Get all outputs
terraform output

# Get specific output
terraform output alb_dns_name
terraform output rds_endpoint
terraform output redis_endpoint
```

## Updating Infrastructure

```bash
# Make changes to .tf files
# Review changes
terraform plan

# Apply changes
terraform apply
```

## Destroying Infrastructure

⚠️ **Warning**: This will delete all resources!

```bash
terraform destroy
```

## State Management

For production, configure remote state:

```bash
# Create S3 bucket for state
aws s3 mb s3://expense-tracker-terraform-state

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket expense-tracker-terraform-state \
  --versioning-configuration Status=Enabled

# Update backend in main.tf
# Then reinitialize
terraform init -migrate-state
```


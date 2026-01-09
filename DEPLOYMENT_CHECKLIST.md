# Deployment Checklist

## Pre-Deployment (Before First Deploy)

### AWS Setup
- [ ] AWS Account created
- [ ] AWS CLI installed and configured
- [ ] Terraform installed
- [ ] AWS credentials configured (`aws configure`)
- [ ] AWS account ID noted

### Terraform Setup
- [ ] Navigate to `terraform/environments/production`
- [ ] Copy `terraform.tfvars.example` to `terraform.tfvars`
- [ ] Fill in `terraform.tfvars`:
  - [ ] `db_password` (strong password)
  - [ ] `secret_key` (min 32 chars, random)
  - [ ] Review other variables
- [ ] Run `terraform init`
- [ ] Run `terraform plan` (review changes)
- [ ] Run `terraform apply` (creates all infrastructure)

### GitHub Secrets
- [ ] Go to: Repository → Settings → Secrets and variables → Actions
- [ ] Add all secrets from `CICD_SETUP_PLAN.md`
- [ ] Get values from:
  - AWS credentials: `aws configure list`
  - AWS Account ID: `aws sts get-caller-identity`
  - Database URL: `terraform output rds_endpoint`
  - Redis URL: `terraform output redis_endpoint`

### Code Preparation
- [ ] All code committed
- [ ] Tests passing locally
- [ ] Docker image builds successfully
- [ ] `.env.example` updated

## First Deployment

- [ ] Push code to `main` branch
- [ ] Monitor GitHub Actions:
  - [ ] CI workflow passes
  - [ ] CD workflow passes
  - [ ] Deployment completes
- [ ] Verify deployment:
  - [ ] Health check: `curl https://<alb-dns>/health`
  - [ ] API docs: `curl https://<alb-dns>/docs`
  - [ ] Test authentication endpoint

## Post-Deployment

- [ ] Verify ECS service is running
- [ ] Check CloudWatch logs
- [ ] Test API endpoints
- [ ] Monitor costs in AWS Console
- [ ] Set up CloudWatch alarms
- [ ] Document ALB DNS name

## Ongoing Maintenance

- [ ] Monitor GitHub Actions
- [ ] Review CloudWatch metrics weekly
- [ ] Check AWS costs monthly
- [ ] Update dependencies quarterly
- [ ] Review security alerts


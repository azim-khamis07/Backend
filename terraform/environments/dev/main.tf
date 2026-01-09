terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "expense-tracker-terraform-state-301691474806"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "expense-tracker-terraform-lock"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "expense-tracker"
      Environment = "development"
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  vpc_cidr             = var.vpc_cidr
  availability_zones   = data.aws_availability_zones.available.names
  enable_nat_gateway   = false  # No NAT for dev (cost savings)
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.project_name}-vpc-dev"
  }
}

# RDS Module (smaller instance for dev)
module "rds" {
  source = "../../modules/rds"
  
  vpc_id              = module.vpc.vpc_id
  vpc_cidr            = var.vpc_cidr
  private_subnet_ids  = module.vpc.private_subnet_ids
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
  instance_class      = "db.t3.micro"  # Smaller for dev
  allocated_storage   = 20
  multi_az            = false  # Single AZ for dev
  backup_retention_period = 0  # Free Tier compatible (0-1 days)
  skip_final_snapshot = true  # Skip snapshot for dev
  performance_insights_enabled = false  # Disable for dev (cost savings)
  
  tags = {
    Name = "${var.project_name}-rds-dev"
  }
}

# ElastiCache Module (smaller for dev)
module "elasticache" {
  source = "../../modules/elasticache"
  
  vpc_id              = module.vpc.vpc_id
  vpc_cidr            = var.vpc_cidr
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_type           = "cache.t3.micro"  # Smaller for dev
  num_cache_nodes     = 1
  
  tags = {
    Name = "${var.project_name}-redis-dev"
  }
}

# ECR Module
module "ecr" {
  source = "../../modules/ecr"
  
  repository_name = "${var.ecr_repository_name}-dev"
  
  tags = {
    Name = "${var.project_name}-ecr-dev"
  }
}

# ALB Module (must be before ECS)
module "alb" {
  source = "../../modules/alb"
  
  vpc_id           = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  project_name     = "${var.project_name}-dev"
  
  tags = {
    Name = "${var.project_name}-alb-dev"
  }
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"
  
  cluster_name        = "${var.ecs_cluster_name}-dev"
  service_name        = "${var.ecs_service_name}-dev"
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids    = module.vpc.public_subnet_ids
  private_subnet_ids   = module.vpc.private_subnet_ids
  ecr_repository_url   = module.ecr.repository_url
  alb_security_group_id = module.alb.security_group_id
  target_group_arn     = module.alb.target_group_arn
  
  # Application configuration (smaller for dev)
  app_image_tag       = var.app_image_tag
  app_cpu             = 512  # 0.5 vCPU for dev
  app_memory          = 1024  # 1 GB for dev
  desired_count       = 1  # Single instance for dev
  environment         = "development"  # Set environment to development for dev
  
  # Environment variables
  database_url        = "postgresql://${var.db_username}:${var.db_password}@${module.rds.endpoint}:5432/${var.db_name}"
  redis_url           = "redis://${module.elasticache.endpoint}:6379/0"
  celery_broker_url   = "redis://${module.elasticache.endpoint}:6379/1"
  celery_result_backend = "redis://${module.elasticache.endpoint}:6379/2"
  
  secret_key          = var.secret_key
  aws_region          = var.aws_region
  s3_bucket_name      = module.s3.bucket_name
  
  tags = {
    Name = "${var.project_name}-ecs-dev"
  }
}

# S3 Module
module "s3" {
  source = "../../modules/s3"
  
  bucket_name = "${var.s3_bucket_name}-dev"
  
  tags = {
    Name = "${var.project_name}-s3-dev"
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.endpoint
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.ecr.repository_url
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.dns_name
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.s3.bucket_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}


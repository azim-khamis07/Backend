variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "expense-tracker"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.1.0.0/16"  # Different CIDR for dev
}

# Database variables
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "expensedb_dev"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "expenseuser"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

# ECR variables
variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "expense-tracker-backend"
}

# ECS variables
variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "expense-tracker-cluster"
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
  default     = "expense-tracker-api"
}

variable "app_image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

# S3 variables
variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "expense-tracker-receipts"
}

# Application secrets
variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}


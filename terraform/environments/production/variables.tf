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
  default     = "10.0.0.0/16"
}

# Database variables
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "expensedb"
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

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.small"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_multi_az" {
  description = "Enable RDS Multi-AZ"
  type        = bool
  default     = false
}

# Redis variables
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.small"
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
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

variable "ecs_task_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 1024  # 1 vCPU
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 2048  # 2 GB
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
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


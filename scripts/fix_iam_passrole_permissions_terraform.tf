# IAM Policy for GitHub Actions user to pass roles to ECS
# This Terraform configuration grants the GitHub Actions user permission to pass IAM roles to ECS tasks
#
# Usage:
# 1. Set the following variables in terraform.tfvars:
#    github_actions_user_name = "github-actions-expense-tracker"
#    aws_account_id = "301691474806"
#
# 2. Run: terraform init && terraform plan && terraform apply

variable "github_actions_user_name" {
  description = "Name of the GitHub Actions IAM user"
  type        = string
  default     = "github-actions-expense-tracker"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "project_name" {
  description = "Project name (used for role name patterns)"
  type        = string
  default     = "expense-tracker"
}

# IAM Policy allowing PassRole for ECS task roles
resource "aws_iam_policy" "github_actions_ecs_passrole" {
  name        = "${var.github_actions_user_name}-ecs-passrole-policy"
  description = "Allow GitHub Actions user to pass IAM roles to ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPassRoleForECSTaskRoles"
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          "arn:aws:iam::${var.aws_account_id}:role/${var.project_name}-*-ecs-task-role",
          "arn:aws:iam::${var.aws_account_id}:role/${var.project_name}-*-ecs-execution-role"
        ]
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.github_actions_user_name}-ecs-passrole-policy"
    Description = "IAM policy for GitHub Actions to pass roles to ECS"
  }
}

# Attach policy to GitHub Actions user
resource "aws_iam_user_policy_attachment" "github_actions_ecs_passrole" {
  user       = var.github_actions_user_name
  policy_arn = aws_iam_policy.github_actions_ecs_passrole.arn
}

output "policy_arn" {
  description = "ARN of the created IAM policy"
  value       = aws_iam_policy.github_actions_ecs_passrole.arn
}

output "policy_name" {
  description = "Name of the created IAM policy"
  value       = aws_iam_policy.github_actions_ecs_passrole.name
}


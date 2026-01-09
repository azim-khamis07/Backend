# Fix IAM PassRole Permissions for ECS Deployment

## 🔍 Problem

When deploying to ECS, you're getting this error:

```
User: arn:aws:iam::301691474806:user/github-actions-expense-tracker is not authorized to perform: iam:PassRole on resource: arn:aws:iam::301691474806:role/expense-tracker-ecs-dev-ecs-task-role because no identity-based policy allows the iam:PassRole action
```

## 🔐 Root Cause

The GitHub Actions IAM user needs permission to **pass IAM roles** to ECS when creating/updating task definitions. This is required because ECS tasks need IAM roles (task role and execution role) to access AWS services.

## ✅ Solution Options

### Option 1: Using AWS CLI Script (Recommended)

**Quick fix using the provided script:**

```bash
# Set your AWS credentials (or use AWS CLI configured profile)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1

# Optional: Set AWS Account ID (will be auto-detected if not set)
export AWS_ACCOUNT_ID=301691474806

# Optional: Set GitHub Actions user name (default: github-actions-expense-tracker)
export GITHUB_ACTIONS_USER_NAME=github-actions-expense-tracker

# Run the fix script
./scripts/fix_iam_passrole_permissions.sh
```

### Option 2: Using AWS Console

1. **Go to IAM Console**: https://console.aws.amazon.com/iam/
2. **Navigate to Users** → Select `github-actions-expense-tracker`
3. **Click "Add permissions"** → "Create inline policy"
4. **Switch to JSON tab** and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPassRoleForECSTaskRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-*-ecs-task-role",
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-*-ecs-execution-role"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ecs-tasks.amazonaws.com"
        }
      }
    }
  ]
}
```

5. **Name the policy**: `github-actions-expense-tracker-ecs-passrole-policy`
6. **Click "Create policy"**

### Option 3: Using Terraform (Infrastructure as Code)

If you want to manage this with Terraform:

1. **Create a new Terraform file** (e.g., `terraform/iam-github-actions.tf`):

```hcl
# Set variables in terraform.tfvars
variable "github_actions_user_name" {
  default = "github-actions-expense-tracker"
}

variable "aws_account_id" {
  default = "301691474806"
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
          "arn:aws:iam::${var.aws_account_id}:role/expense-tracker-ecs-*-ecs-task-role",
          "arn:aws:iam::${var.aws_account_id}:role/expense-tracker-ecs-*-ecs-execution-role"
        ]
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Attach policy to GitHub Actions user
resource "aws_iam_user_policy_attachment" "github_actions_ecs_passrole" {
  user       = var.github_actions_user_name
  policy_arn = aws_iam_policy.github_actions_ecs_passrole.arn
}
```

2. **Apply with Terraform**:
```bash
terraform init
terraform plan
terraform apply
```

## 📋 What Permissions Are Needed?

The GitHub Actions user needs `iam:PassRole` permission on:

1. **ECS Task Role**: `expense-tracker-ecs-{env}-ecs-task-role`
   - Used by ECS tasks to access AWS services (S3, etc.)

2. **ECS Execution Role**: `expense-tracker-ecs-{env}-ecs-execution-role`
   - Used by ECS to pull images from ECR and write logs to CloudWatch

**Important**: The `Condition` block ensures the role can only be passed to `ecs-tasks.amazonaws.com`, which is a security best practice.

## 🔍 Verify the Fix

After applying the fix, verify the permissions:

```bash
# Check attached policies
aws iam list-attached-user-policies --user-name github-actions-expense-tracker

# Check inline policies
aws iam list-user-policies --user-name github-actions-expense-tracker

# Get policy document
aws iam get-policy --policy-arn arn:aws:iam::301691474806:policy/github-actions-expense-tracker-ecs-passrole-policy
```

## 🚀 Next Steps

1. **Run the fix script or apply the policy manually**
2. **Wait a few seconds** for IAM permissions to propagate
3. **Retry the ECS deployment** - it should now succeed!

## 📚 Additional Resources

- [AWS IAM PassRole Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html)
- [ECS Task IAM Roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)


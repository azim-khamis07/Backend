# Quick Fix: IAM PassRole Permission for ECS Deployment

## 🔍 Problem

Error during ECS deployment:
```
User: arn:aws:iam::301691474806:user/github-actions-expense-tracker is not authorized to perform: iam:PassRole on resource: arn:aws:iam::301691474806:role/expense-tracker-ecs-dev-ecs-task-role
```

## ⚡ Quick Fix (Copy & Paste)

Run these commands in your terminal:

```bash
# 1. Create the IAM policy
aws iam create-policy \
  --policy-name github-actions-expense-tracker-ecs-passrole-policy \
  --policy-document '{
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
  }' \
  --description "Allow GitHub Actions user to pass IAM roles to ECS tasks"

# 2. Get the policy ARN from the output above, then attach it to the user
# Replace POLICY_ARN with the ARN from step 1 output
aws iam attach-user-policy \
  --user-name github-actions-expense-tracker \
  --policy-arn arn:aws:iam::301691474806:policy/github-actions-expense-tracker-ecs-passrole-policy
```

## 📋 One-Liner Version

If the policy already exists, you can update it:

```bash
# Get the policy ARN first
POLICY_ARN=$(aws iam list-policies --query 'Policies[?PolicyName==`github-actions-expense-tracker-ecs-passrole-policy`].Arn' --output text)

# Create new policy version
aws iam create-policy-version \
  --policy-arn "$POLICY_ARN" \
  --policy-document file:///tmp/iam-policy-passrole.json \
  --set-as-default

# Attach to user (if not already attached)
aws iam attach-user-policy \
  --user-name github-actions-expense-tracker \
  --policy-arn "$POLICY_ARN"
```

## ✅ Verify

Check that the policy is attached:

```bash
aws iam list-attached-user-policies --user-name github-actions-expense-tracker
```

You should see `github-actions-expense-tracker-ecs-passrole-policy` in the list.

## 🚀 After Fixing

1. Wait 10-30 seconds for IAM permissions to propagate
2. Retry the ECS deployment in GitHub Actions
3. It should now succeed!

## 📚 Full Documentation

See `IAM_PASSROLE_FIX.md` for detailed explanation and alternative solutions.


# Quick Fix: IAM PassRole Error for Dev Environment

## 🚨 Error

```
User: arn:aws:iam::301691474806:user/github-actions-expense-tracker is not authorized to perform: iam:PassRole on resource: arn:aws:iam::301691474806:role/expense-tracker-ecs-dev-ecs-task-role
```

## ✅ Quick Fix (Copy-Paste Commands)

Run these commands in your terminal (requires AWS CLI configured):

```bash
# Set variables
export AWS_ACCOUNT_ID=301691474806
export GITHUB_ACTIONS_USER_NAME=github-actions-expense-tracker

# Create policy document
cat > /tmp/passrole-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPassRoleForECSTaskRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-dev-ecs-task-role",
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-dev-ecs-execution-role",
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-staging-ecs-task-role",
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-staging-ecs-execution-role",
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-production-ecs-task-role",
        "arn:aws:iam::301691474806:role/expense-tracker-ecs-production-ecs-execution-role"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ecs-tasks.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# Policy name
POLICY_NAME="github-actions-expense-tracker-ecs-passrole-policy"
POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"

# Check if policy exists and create/update
if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    echo "Policy exists, updating..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file:///tmp/passrole-policy.json \
        --set-as-default
    echo "✅ Policy updated"
else
    echo "Creating new policy..."
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file:///tmp/passrole-policy.json \
        --description "Allow GitHub Actions user to pass IAM roles to ECS tasks"
    echo "✅ Policy created"
fi

# Attach policy to user (check if already attached)
ATTACHED=$(aws iam list-attached-user-policies --user-name "$GITHUB_ACTIONS_USER_NAME" --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text)

if [ -z "$ATTACHED" ]; then
    echo "Attaching policy to user..."
    aws iam attach-user-policy \
        --user-name "$GITHUB_ACTIONS_USER_NAME" \
        --policy-arn "$POLICY_ARN"
    echo "✅ Policy attached to user"
else
    echo "✅ Policy already attached to user"
fi

echo ""
echo "✅ Done! Wait 10-30 seconds for IAM to propagate, then retry the deployment."
```

## 🔍 Verify the Fix

```bash
# Check if policy is attached
aws iam list-attached-user-policies --user-name github-actions-expense-tracker

# Check policy contents
aws iam get-policy-version \
    --policy-arn arn:aws:iam::301691474806:policy/github-actions-expense-tracker-ecs-passrole-policy \
    --version-id $(aws iam get-policy --policy-arn arn:aws:iam::301691474806:policy/github-actions-expense-tracker-ecs-passrole-policy --query 'Policy.DefaultVersionId' --output text)
```

## 🚀 After Fix

1. Wait 10-30 seconds for IAM permissions to propagate
2. Retry the GitHub Actions workflow (or push a new commit)
3. The deployment should now succeed!

## 📚 Alternative: Use the Script

```bash
export AWS_ACCOUNT_ID=301691474806
./scripts/fix_iam_passrole_permissions.sh
```

The script will automatically create and attach the policy.


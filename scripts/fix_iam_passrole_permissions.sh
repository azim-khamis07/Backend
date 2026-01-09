#!/bin/bash
# Fix IAM PassRole permissions for GitHub Actions user
# This script grants the GitHub Actions user permission to pass IAM roles to ECS tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🔧 Fix IAM PassRole Permissions"
echo "=========================================="
echo ""

# Configuration
GITHUB_ACTIONS_USER_NAME="${GITHUB_ACTIONS_USER_NAME:-github-actions-expense-tracker}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

# Get AWS Account ID if not provided
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "📋 Getting AWS Account ID..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo -e "${RED}❌ Error: Could not get AWS Account ID${NC}"
        echo "   Please set AWS_ACCOUNT_ID environment variable or configure AWS CLI"
        exit 1
    fi
fi

echo "✅ AWS Account ID: $AWS_ACCOUNT_ID"
echo "✅ GitHub Actions User: $GITHUB_ACTIONS_USER_NAME"
echo "✅ AWS Region: $AWS_REGION"
echo ""

# Get the user ARN
GITHUB_ACTIONS_USER_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:user/${GITHUB_ACTIONS_USER_NAME}"

# Check if user exists
echo "🔍 Checking if IAM user exists..."
if ! aws iam get-user --user-name "$GITHUB_ACTIONS_USER_NAME" >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: IAM user '$GITHUB_ACTIONS_USER_NAME' does not exist${NC}"
    exit 1
fi

echo "✅ IAM user exists"
echo ""

# Create policy document for PassRole permissions
POLICY_NAME="${GITHUB_ACTIONS_USER_NAME}-ecs-passrole-policy"

echo "📝 Creating IAM policy for PassRole permissions..."

# Create policy document
cat > /tmp/passrole-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPassRoleForECSTaskRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::${AWS_ACCOUNT_ID}:role/expense-tracker-ecs-*-ecs-task-role",
        "arn:aws:iam::${AWS_ACCOUNT_ID}:role/expense-tracker-ecs-*-ecs-execution-role"
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

echo "✅ Policy document created"
echo ""

# Check if policy already exists
if aws iam get-policy --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}" >/dev/null 2>&1; then
    echo "⚠️  Policy '$POLICY_NAME' already exists. Updating..."
    
    # Get the default version of the policy
    POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"
    DEFAULT_VERSION=$(aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId' --output text)
    
    # Create new policy version
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file:///tmp/passrole-policy.json \
        --set-as-default >/dev/null
    
    # Delete old versions (keep only the 5 most recent)
    VERSIONS=$(aws iam list-policy-versions --policy-arn "$POLICY_ARN" --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text)
    for version in $VERSIONS; do
        aws iam delete-policy-version --policy-arn "$POLICY_ARN" --version-id "$version" 2>/dev/null || true
    done
    
    echo "✅ Policy updated"
else
    echo "📝 Creating new IAM policy..."
    POLICY_OUTPUT=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file:///tmp/passrole-policy.json \
        --description "Allow GitHub Actions user to pass IAM roles to ECS tasks" 2>&1)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error creating policy:${NC}"
        echo "$POLICY_OUTPUT"
        exit 1
    fi
    
    POLICY_ARN=$(echo "$POLICY_OUTPUT" | grep -oP 'arn:aws:iam::[^"]*' | head -1)
    echo "✅ Policy created: $POLICY_ARN"
fi

echo ""

# Attach policy to user
echo "🔗 Attaching policy to IAM user..."

# Check if policy is already attached
ATTACHED_POLICIES=$(aws iam list-attached-user-policies --user-name "$GITHUB_ACTIONS_USER_NAME" --query 'AttachedPolicies[?PolicyArn==`'$POLICY_ARN'`].PolicyArn' --output text)

if [ -n "$ATTACHED_POLICIES" ]; then
    echo "⚠️  Policy already attached to user"
else
    aws iam attach-user-policy \
        --user-name "$GITHUB_ACTIONS_USER_NAME" \
        --policy-arn "$POLICY_ARN"
    
    if [ $? -eq 0 ]; then
        echo "✅ Policy attached to user"
    else
        echo -e "${RED}❌ Error attaching policy to user${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}✅ IAM PassRole permissions fixed!${NC}"
echo ""
echo "📋 Summary:"
echo "   - Policy Name: $POLICY_NAME"
echo "   - Policy ARN: $POLICY_ARN"
echo "   - Attached to: $GITHUB_ACTIONS_USER_ARN"
echo ""
echo "🔍 Permissions granted:"
echo "   - iam:PassRole on expense-tracker-ecs-*-ecs-task-role"
echo "   - iam:PassRole on expense-tracker-ecs-*-ecs-execution-role"
echo "   - Only when passing to: ecs-tasks.amazonaws.com"
echo ""
echo "🚀 You can now retry the ECS deployment!"


#!/bin/bash
#
# Get values for GitHub Secrets configuration
# Usage: ./scripts/get_github_secrets.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔐 GitHub Secrets Configuration Helper${NC}"
echo "======================================"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI not found. Install it first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS credentials not configured. Run: aws configure${NC}"
    exit 1
fi

# Get AWS Account ID
echo -e "${GREEN}📋 AWS Account ID:${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "   AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID"
echo ""

# Get AWS Region
echo -e "${GREEN}📋 AWS Region:${NC}"
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
echo "   AWS_REGION=$AWS_REGION"
echo ""

# Get current AWS access key (if available)
echo -e "${GREEN}📋 Current AWS Credentials:${NC}"
CURRENT_ACCESS_KEY=$(aws configure get aws_access_key_id 2>/dev/null || echo "NOT_SET")
if [ "$CURRENT_ACCESS_KEY" != "NOT_SET" ]; then
    echo "   Current Access Key: ${CURRENT_ACCESS_KEY:0:10}... (last 4: ${CURRENT_ACCESS_KEY: -4})"
    echo "   ${YELLOW}⚠️  Note: Use a dedicated IAM user for GitHub Actions${NC}"
else
    echo "   ${YELLOW}⚠️  No access key found. Create IAM user for GitHub Actions.${NC}"
fi
echo ""

# Get values from dev environment
if [ -f "terraform/environments/dev/terraform.tfvars" ]; then
    cd terraform/environments/dev
    
    if terraform output -json &> /dev/null; then
        echo -e "${GREEN}📋 From Dev Environment (terraform output):${NC}"
        
        # Check if jq is available
        if command -v jq &> /dev/null; then
            terraform output -json | jq -r '
                "   ECR_REPOSITORY_DEV=expense-tracker-backend-dev",
                "   ECS_CLUSTER_DEV=expense-tracker-cluster-dev", 
                "   ECS_SERVICE_DEV=expense-tracker-api-dev",
                "   ECS_TASK_DEFINITION_DEV=expense-tracker-api-dev",
                "   RDS_ENDPOINT=" + (.rds_endpoint.value // "not-set"),
                "   REDIS_ENDPOINT=" + (.redis_endpoint.value // "not-set"),
                "   ALB_DNS=" + (.alb_dns_name.value // "not-set")
            '
            
            # Get database URL format
            RDS_ENDPOINT=$(terraform output -json | jq -r '.rds_endpoint.value // "not-set"')
            REDIS_ENDPOINT=$(terraform output -json | jq -r '.redis_endpoint.value // "not-set"')
            
            echo ""
            echo -e "${GREEN}📋 Connection Strings (Format):${NC}"
            if [ "$RDS_ENDPOINT" != "not-set" ]; then
                echo "   DATABASE_URL=postgresql://expenseuser:<PASSWORD>@$RDS_ENDPOINT/expensedb_dev"
            fi
            if [ "$REDIS_ENDPOINT" != "not-set" ]; then
                echo "   REDIS_URL=redis://$REDIS_ENDPOINT:6379/0"
                echo "   CELERY_BROKER_URL=redis://$REDIS_ENDPOINT:6379/1"
                echo "   CELERY_RESULT_BACKEND=redis://$REDIS_ENDPOINT:6379/2"
            fi
        else
            echo "   (jq not installed - showing raw output)"
            terraform output
        fi
        
        cd ../..
    else
        echo -e "${YELLOW}⚠️  Terraform not initialized. Run: terraform init${NC}"
        cd ../..
    fi
else
    echo -e "${YELLOW}⚠️  terraform.tfvars not found in dev environment${NC}"
fi

echo ""
echo -e "${BLUE}📝 Required GitHub Secrets:${NC}"
echo "======================================"
echo ""
echo "Go to: ${BLUE}GitHub Repo → Settings → Secrets and variables → Actions → New repository secret${NC}"
echo ""
echo "Add these secrets:"
echo ""
echo "1. ${GREEN}AWS_ACCESS_KEY_ID${NC}"
echo "   Value: <Create IAM user and get access key>"
echo "   How: aws iam create-user --user-name github-actions-expense-tracker"
echo "        aws iam create-access-key --user-name github-actions-expense-tracker"
echo ""
echo "2. ${GREEN}AWS_SECRET_ACCESS_KEY${NC}"
echo "   Value: <From IAM user access key creation>"
echo ""
echo "3. ${GREEN}AWS_REGION${NC}"
echo "   Value: $AWS_REGION"
echo ""
echo "4. ${GREEN}AWS_ACCOUNT_ID${NC}"
echo "   Value: $AWS_ACCOUNT_ID"
echo ""
echo -e "${YELLOW}ℹ️  Optional Secrets (if your application needs them):${NC}"
echo ""
echo "5. SECRET_KEY"
echo "   Value: <From terraform.tfvars or generate new>"
echo "   How: Check terraform/environments/dev/terraform.tfvars"
echo ""
echo "6. DATABASE_URL"
echo "   Value: postgresql://expenseuser:<PASSWORD>@<rds-endpoint>:5432/expensedb_dev"
echo "   Format: Replace <PASSWORD> with actual password from terraform.tfvars"
echo "           Replace <rds-endpoint> with RDS_ENDPOINT above"
echo ""
echo "7. REDIS_URL"
echo "   Value: redis://<redis-endpoint>:6379/0"
echo "   Format: Replace <redis-endpoint> with REDIS_ENDPOINT above"
echo ""
echo -e "${BLUE}✅ After adding secrets, your CI/CD pipeline will be ready!${NC}"
echo ""
echo "📚 Next steps:"
echo "   1. Add the secrets above to GitHub"
echo "   2. Test CI: Create a PR or push to any branch"
echo "   3. Test CD: Push to 'develop' branch (deploys to dev)"
echo "   4. Monitor: GitHub → Actions tab"
echo ""


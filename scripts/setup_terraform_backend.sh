#!/bin/bash
#
# Setup Terraform S3 Backend and DynamoDB Lock Table
# Usage: ./scripts/setup_terraform_backend.sh [region]
#

set -e

REGION=${1:-us-east-1}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Terraform Backend Setup${NC}"
echo "=================================="
echo ""

# Get AWS account ID
echo "📋 Getting AWS account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Error: Could not get AWS account ID${NC}"
    echo "Make sure AWS CLI is configured: aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS Account ID: ${ACCOUNT_ID}${NC}"
echo ""

# Generate bucket name
BUCKET_NAME="expense-tracker-terraform-state-${ACCOUNT_ID}"
TABLE_NAME="expense-tracker-terraform-lock"

echo "📦 Configuration:"
echo "   Bucket Name: ${BUCKET_NAME}"
echo "   DynamoDB Table: ${TABLE_NAME}"
echo "   Region: ${REGION}"
echo ""

# Check if bucket already exists
if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Bucket ${BUCKET_NAME} already exists${NC}"
    read -p "Continue with existing bucket? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
    BUCKET_EXISTS=true
else
    BUCKET_EXISTS=false
fi

# Create S3 bucket if it doesn't exist
if [ "$BUCKET_EXISTS" = false ]; then
    echo "📦 Creating S3 bucket..."
    
    # Try to create in specified region
    if aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" 2>/dev/null; then
        echo -e "${GREEN}✅ Bucket created: ${BUCKET_NAME}${NC}"
    else
        # If region fails, try us-east-1 (no location constraint needed)
        echo "Trying us-east-1 (default)..."
        if aws s3 mb "s3://${BUCKET_NAME}" --region us-east-1 2>/dev/null; then
            REGION="us-east-1"
            echo -e "${GREEN}✅ Bucket created in us-east-1: ${BUCKET_NAME}${NC}"
        else
            echo -e "${RED}❌ Error: Could not create bucket${NC}"
            echo "The bucket name might already be taken. Try a different suffix."
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Using existing bucket${NC}"
fi

# Enable versioning
echo ""
echo "📦 Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled \
    --region "$REGION" >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  Could not enable versioning (might already be enabled)${NC}"
echo -e "${GREEN}✅ Versioning enabled${NC}"

# Enable encryption
echo ""
echo "🔒 Enabling encryption..."
aws s3api put-bucket-encryption \
    --bucket "${BUCKET_NAME}" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }' \
    --region "$REGION" >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  Could not enable encryption (might already be enabled)${NC}"
echo -e "${GREEN}✅ Encryption enabled${NC}"

# Block public access
echo ""
echo "🔒 Blocking public access..."
aws s3api put-public-access-block \
    --bucket "${BUCKET_NAME}" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region "$REGION" >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  Could not block public access (might already be configured)${NC}"
echo -e "${GREEN}✅ Public access blocked${NC}"

# Check if DynamoDB table exists
echo ""
echo "📋 Checking DynamoDB table..."
if aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "$REGION" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  DynamoDB table ${TABLE_NAME} already exists${NC}"
    read -p "Continue with existing table? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
    TABLE_EXISTS=true
else
    TABLE_EXISTS=false
fi

# Create DynamoDB table if it doesn't exist
if [ "$TABLE_EXISTS" = false ]; then
    echo "📦 Creating DynamoDB table for state locking..."
    
    aws dynamodb create-table \
        --table-name "${TABLE_NAME}" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "⏳ Waiting for table to be active..."
        aws dynamodb wait table-exists --table-name "${TABLE_NAME}" --region "$REGION"
        echo -e "${GREEN}✅ DynamoDB table created: ${TABLE_NAME}${NC}"
    else
        echo -e "${RED}❌ Error: Could not create DynamoDB table${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Using existing DynamoDB table${NC}"
fi

# Summary
echo ""
echo "=================================="
echo -e "${GREEN}✅ Terraform Backend Setup Complete!${NC}"
echo "=================================="
echo ""
echo "📝 Use these values in your Terraform backend configuration:"
echo ""
echo -e "${BLUE}Backend Configuration:${NC}"
echo "---"
echo "bucket         = \"${BUCKET_NAME}\""
echo "key            = \"<environment>/terraform.tfstate\""
echo "region         = \"${REGION}\""
echo "encrypt        = true"
echo "dynamodb_table = \"${TABLE_NAME}\""
echo ""
echo "📋 For each environment:"
echo ""
echo "  Dev:        key = \"dev/terraform.tfstate\""
echo "  Staging:    key = \"staging/terraform.tfstate\""
echo "  Production: key = \"production/terraform.tfstate\""
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Update backend configuration in:"
echo "   - terraform/environments/dev/main.tf"
echo "   - terraform/environments/staging/main.tf"
echo "   - terraform/environments/production/main.tf"
echo ""
echo "2. Reinitialize Terraform:"
echo "   cd terraform/environments/dev"
echo "   terraform init"
echo ""
echo "✅ Done!"


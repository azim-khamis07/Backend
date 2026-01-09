#!/bin/bash
#
# Deploy to Specific Environment
# Usage: ./scripts/deploy_environment.sh [dev|staging|production]
#

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Usage: $0 [dev|staging|production]"
    exit 1
fi

echo "🚀 Deploying to $ENVIRONMENT environment..."
echo ""

TERRAFORM_DIR="terraform/environments/$ENVIRONMENT"

# Check if terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo -e "${RED}❌ Terraform directory not found: $TERRAFORM_DIR${NC}"
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
    echo -e "${YELLOW}⚠️  terraform.tfvars not found${NC}"
    echo "Creating from example..."
    cp "$TERRAFORM_DIR/terraform.tfvars.example" "$TERRAFORM_DIR/terraform.tfvars"
    echo -e "${YELLOW}⚠️  Please edit $TERRAFORM_DIR/terraform.tfvars with your values${NC}"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Plan
echo ""
echo "📋 Planning infrastructure changes..."
terraform plan -out=tfplan

# Confirm
echo ""
read -p "Apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Apply
echo ""
echo "🚀 Applying infrastructure changes..."
terraform apply tfplan

# Get outputs
echo ""
echo "📊 Deployment outputs:"
terraform output

echo ""
echo -e "${GREEN}✅ Deployment to $ENVIRONMENT complete!${NC}"


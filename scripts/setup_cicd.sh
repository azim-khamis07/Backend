#!/bin/bash
#
# CI/CD Setup Script
# This script helps set up the CI/CD pipeline infrastructure
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "🚀 CI/CD Setup Script"
echo "===================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    echo "Install: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI installed${NC}"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed${NC}"
    echo "Install: https://www.terraform.io/downloads"
    exit 1
fi
echo -e "${GREEN}✅ Terraform installed${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi
echo -e "${GREEN}✅ AWS credentials configured${NC}"

echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Configure GitHub Secrets:"
echo "   - Go to: Repository Settings → Secrets and variables → Actions"
echo "   - Add secrets from CICD_SETUP_PLAN.md"
echo ""
echo "2. Set up Terraform:"
echo "   cd terraform/environments/production"
echo "   cp terraform.tfvars.example terraform.tfvars"
echo "   # Edit terraform.tfvars with your values"
echo "   terraform init"
echo "   terraform plan"
echo ""
echo "3. First Deployment:"
echo "   # Push code to main branch"
echo "   git push origin main"
echo "   # Monitor GitHub Actions"
echo ""
echo -e "${GREEN}✅ Setup check complete!${NC}"


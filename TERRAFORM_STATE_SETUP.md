# Terraform State Backend Setup

## What is This?

When Terraform asks for an **S3 bucket name**, it's asking where to store your **Terraform state file**. 

The state file tracks:
- What infrastructure you've created
- Resource IDs and attributes
- Dependencies between resources

**Why use S3 for state?**
- ✅ **Remote storage**: State is stored safely in AWS
- ✅ **Team collaboration**: Multiple people can work together
- ✅ **State locking**: Prevents conflicts when multiple people run Terraform
- ✅ **Backup**: Versioning and history of changes

---

## Step 1: Create the S3 Bucket

The bucket name must be **globally unique** across all AWS accounts. Use this format:

```
expense-tracker-terraform-state-<your-aws-account-id>
```

Or with a unique suffix:

```
expense-tracker-terraform-state-<unique-suffix>
```

### Quick Setup Script

Run this script to create the bucket with all required settings:

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="expense-tracker-terraform-state-${ACCOUNT_ID}"

# Create the bucket
aws s3 mb s3://${BUCKET_NAME} --region us-east-1

# Enable versioning (for backup/history)
aws s3api put-bucket-versioning \
  --bucket ${BUCKET_NAME} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ${BUCKET_NAME} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access (security)
aws s3api put-public-access-block \
  --bucket ${BUCKET_NAME} \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "✅ Bucket created: ${BUCKET_NAME}"
echo "📝 Use this bucket name: ${BUCKET_NAME}"
```

---

## Step 2: Create DynamoDB Table (for State Locking)

State locking prevents multiple people from running Terraform at the same time (prevents conflicts).

```bash
# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name expense-tracker-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

echo "✅ DynamoDB table created for state locking"
```

---

## Step 3: Configure Terraform Backend

### Option A: Interactive (Current Prompt)

When Terraform asks for the bucket name, enter:

```
expense-tracker-terraform-state-<your-account-id>
```

**Other prompts:**
- **key**: `dev/terraform.tfstate` (for dev environment)
- **region**: `us-east-1` (or your preferred region)
- **dynamodb_table**: `expense-tracker-terraform-lock` (optional but recommended)

### Option B: Update Backend Configuration

Edit the backend block in your `main.tf`:

```hcl
backend "s3" {
  bucket         = "expense-tracker-terraform-state-<your-account-id>"
  key            = "dev/terraform.tfstate"        # For dev environment
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "expense-tracker-terraform-lock"  # For state locking
}
```

**For different environments:**

**Dev environment** (`terraform/environments/dev/main.tf`):
```hcl
backend "s3" {
  bucket         = "expense-tracker-terraform-state-<your-account-id>"
  key            = "dev/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "expense-tracker-terraform-lock"
}
```

**Staging environment** (`terraform/environments/staging/main.tf`):
```hcl
backend "s3" {
  bucket         = "expense-tracker-terraform-state-<your-account-id>"
  key            = "staging/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "expense-tracker-terraform-lock"
}
```

**Production environment** (`terraform/environments/production/main.tf`):
```hcl
backend "s3" {
  bucket         = "expense-tracker-terraform-state-<your-account-id>"
  key            = "production/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "expense-tracker-terraform-lock"
}
```

**Note**: Same bucket, different `key` paths for each environment!

---

## Step 4: Reinitialize Terraform

After configuring the backend:

```bash
cd terraform/environments/dev  # or staging/production
terraform init
```

If migrating from local state, Terraform will ask:
```
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the backend.

  Would you like to copy this state to the new backend?
  Enter "yes" to copy and "no" to start with an empty state.

  Enter a value:
```

Enter `yes` to migrate your existing state.

---

## Quick Reference

### What Value to Enter When Prompted?

**During `terraform init`:**

1. **bucket** (S3 bucket name):
   ```
   expense-tracker-terraform-state-<your-aws-account-id>
   ```
   
   To get your account ID:
   ```bash
   aws sts get-caller-identity --query Account --output text
   ```

2. **key** (state file path):
   - Dev: `dev/terraform.tfstate`
   - Staging: `staging/terraform.tfstate`
   - Production: `production/terraform.tfstate`

3. **region** (AWS region):
   ```
   us-east-1
   ```
   (or your preferred region)

4. **dynamodb_table** (for locking):
   ```
   expense-tracker-terraform-lock
   ```
   (optional but recommended)

---

## Automated Setup Script

We've created a script to do all of this automatically:

```bash
./scripts/setup_terraform_backend.sh
```

This script will:
1. Get your AWS account ID
2. Create the S3 bucket with proper settings
3. Create the DynamoDB table for locking
4. Show you the exact values to use

---

## Verification

After setup, verify everything works:

```bash
# Check bucket exists
aws s3 ls | grep terraform-state

# Check DynamoDB table exists
aws dynamodb list-tables | grep terraform-lock

# Check state file in S3
aws s3 ls s3://expense-tracker-terraform-state-<account-id>/dev/
```

---

## Troubleshooting

### Error: "Bucket already exists"

The bucket name is already taken. Try a different suffix:

```bash
BUCKET_NAME="expense-tracker-terraform-state-$(date +%s)"
```

### Error: "Access Denied"

Make sure your AWS credentials have permissions:
- `s3:CreateBucket`
- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `dynamodb:CreateTable`
- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:DeleteItem`

### Error: "Backend configuration changed"

If you change the backend configuration after initializing, run:

```bash
terraform init -migrate-state
```

This will ask if you want to migrate the state to the new backend.

---

## Best Practices

1. ✅ **Use one bucket per AWS account** (different keys for each environment)
2. ✅ **Enable versioning** on the state bucket (for recovery)
3. ✅ **Use DynamoDB table** for state locking (prevents conflicts)
4. ✅ **Enable encryption** on the state bucket (security)
5. ✅ **Block public access** (security)
6. ✅ **Use descriptive key names** (`dev/`, `staging/`, `production/`)

---

## Summary

**When Terraform asks for the bucket name, use:**

```
expense-tracker-terraform-state-<your-aws-account-id>
```

**To get your AWS account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

**Example:**
If your account ID is `123456789012`, use:
```
expense-tracker-terraform-state-123456789012
```


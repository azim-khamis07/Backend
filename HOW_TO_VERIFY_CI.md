# How to Verify CI Workflow Triggered

**Quick Guide**: Check if your CI workflow is running automatically

---

## 🎯 Quick Check Methods

### Method 1: GitHub Actions Dashboard (Easiest)

**Step 1: Open GitHub Actions**

Go to: **https://github.com/azim-khamis07/Backend/actions**

**Step 2: Look for Your Workflow Run**

You should see:
- ✅ **Workflow run** with commit message "Test CI pipeline"
- ✅ **Status**: 
  - 🟡 **Yellow circle** = Running/Queued
  - 🟢 **Green checkmark** = Success
  - 🔴 **Red X** = Failed
- ✅ **Branch**: `test-ci`
- ✅ **Trigger**: `push` (automatically triggered)

**Step 3: Click on the Workflow Run**

You'll see:
- Job list (lint-and-format, type-check, test, etc.)
- Status of each job
- Running time
- Logs for each step

---

### Method 2: Check via GitHub CLI (Command Line)

If you have GitHub CLI installed:

```bash
# Install GitHub CLI (if not installed)
# Ubuntu/Debian:
sudo apt install gh

# Authenticate
gh auth login

# Check workflow runs
gh run list --workflow=ci.yml

# Watch latest run status
gh run watch

# View latest run details
gh run view

# Check specific workflow
gh run list --workflow=ci.yml --branch=test-ci
```

**Expected Output**:
```
STATUS  TITLE                  WORKFLOW  BRANCH   EVENT  ID        ELAPSED
✓       Test CI pipeline      CI        test-ci  push   12345678   12m30s
```

---

### Method 3: Check Workflow File Triggers

Verify the CI workflow is configured to trigger automatically:

```bash
cd /home/azim/python-projects/Backend

# View CI workflow configuration
cat .github/workflows/ci.yml | grep -A 5 "on:"

# Should show:
# on:
#   push:
#     branches: [main, develop]
#   pull_request:
#     branches: [main, develop]
```

**Note**: The CI workflow triggers on:
- ✅ Push to `main` or `develop`
- ✅ Pull request to `main` or `develop`

**Important**: Your `test-ci` branch should trigger the workflow because:
- The workflow runs on **push** to any branch
- You pushed to `test-ci` branch

---

### Method 4: Check GitHub API (Advanced)

```bash
# Get latest workflow runs (requires authentication)
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/azim-khamis07/Backend/actions/runs?per_page=1

# Or with GitHub CLI
gh api repos/azim-khamis07/Backend/actions/runs --jq '.workflow_runs[0] | {status, conclusion, head_branch, event}'
```

---

## ✅ Verification Checklist

### Check 1: Workflow Exists ✅

```bash
cd /home/azim/python-projects/Backend
ls -la .github/workflows/ci.yml

# Should exist: ✅
```

### Check 2: Workflow Syntax is Valid ✅

```bash
# GitHub validates YAML syntax automatically
# If workflow file has errors, GitHub will show them in Actions tab
```

### Check 3: Push Was Successful ✅

```bash
git log --oneline -1
# Should show: "Test CI pipeline"

git branch --show-current
# Should show: "test-ci"

git remote -v
# Should show: origin git@github.com:azim-khamis07/Backend.git
```

### Check 4: GitHub Shows the Run ✅

Go to: **https://github.com/azim-khamis07/Backend/actions**

You should see:
- ✅ Workflow run with your commit
- ✅ Status (running/success/failure)
- ✅ Branch name: `test-ci`
- ✅ Trigger: `push`

---

## 🔍 What to Look For

### In GitHub Actions Dashboard:

**✅ Workflow Triggered** (Good Signs):
- Workflow run appears in list
- Status is yellow (running) or green (success)
- Branch matches: `test-ci`
- Trigger shows: `push`
- Started time matches your push time

**❌ Workflow Not Triggered** (Problem Signs):
- No workflow runs visible
- No workflow run for your commit
- Status shows "skipped" or "cancelled"

---

## 🐛 Troubleshooting

### Issue 1: No Workflow Run Appears

**Possible Causes**:
1. Workflow file has syntax errors
2. Workflow is disabled in repository settings
3. Push didn't reach GitHub

**Solutions**:
```bash
# Check workflow file exists
ls -la .github/workflows/ci.yml

# Check if push was successful
git log --oneline -1

# Verify remote
git remote -v

# Check GitHub repository settings
# GitHub → Settings → Actions → General
# Ensure "Allow all actions" is enabled
```

---

### Issue 2: Workflow Shows "Skipped"

**Possible Causes**:
1. Workflow filters exclude your branch
2. Workflow conditions not met

**Check**:
```bash
# View workflow triggers
cat .github/workflows/ci.yml | grep -A 10 "on:"

# Should include your branch or use wildcards
```

---

### Issue 3: Workflow Fails Immediately

**Possible Causes**:
1. Missing required secrets
2. Invalid workflow syntax
3. Runner unavailable

**Check**:
- GitHub Actions → Click on failed run → View logs
- Look for error messages
- Check if secrets are configured

---

## 🚀 Quick Verification Script

Run this script to check everything:

```bash
#!/bin/bash

echo "🔍 Verifying CI Workflow Setup..."
echo ""

# Check workflow file exists
if [ -f ".github/workflows/ci.yml" ]; then
    echo "✅ CI workflow file exists"
else
    echo "❌ CI workflow file not found"
    exit 1
fi

# Check last commit
echo ""
echo "📝 Last commit:"
git log --oneline -1

# Check current branch
echo ""
echo "🌿 Current branch: $(git branch --show-current)"

# Check remote
echo ""
echo "🔗 Remote: $(git remote get-url origin)"

# Check if pushed
echo ""
echo "📤 Checking if pushed to GitHub..."
if git ls-remote --heads origin $(git branch --show-current) | grep -q .; then
    echo "✅ Branch exists on GitHub"
else
    echo "❌ Branch not found on GitHub - push it first!"
    exit 1
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "🔍 Next steps:"
echo "   1. Go to: https://github.com/azim-khamis07/Backend/actions"
echo "   2. Look for workflow run with your commit"
echo "   3. Click on it to see status and logs"
```

Save as `verify-ci.sh` and run: `bash verify-ci.sh`

---

## 📊 Expected Timeline

**When you push**:
- 0-30 seconds: GitHub receives push
- 30-60 seconds: Workflow run appears in Actions tab
- 1-2 minutes: Jobs start running
- 10-15 minutes: All jobs complete

**What to watch**:
1. **Immediate**: Workflow run appears (within 1 minute)
2. **1-2 min**: First job starts (lint-and-format)
3. **5-10 min**: All jobs running
4. **10-15 min**: All jobs complete

---

## ✅ Success Indicators

**CI Workflow Triggered Successfully If**:

1. ✅ Workflow run appears in GitHub Actions (within 1 minute of push)
2. ✅ Status shows running/success
3. ✅ Jobs are executing (lint, test, build, etc.)
4. ✅ Logs are accessible
5. ✅ Branch matches: `test-ci`
6. ✅ Trigger shows: `push`

---

## 🎯 Quick Check Command

```bash
# One-liner to check if workflow exists
cd /home/azim/python-projects/Backend && \
echo "Workflow file: $([ -f .github/workflows/ci.yml ] && echo '✅ Exists' || echo '❌ Missing')" && \
echo "Last commit: $(git log --oneline -1 | head -1)" && \
echo "Branch: $(git branch --show-current)" && \
echo "" && \
echo "🌐 Check workflow status at:" && \
echo "https://github.com/azim-khamis07/Backend/actions"
```

---

**🔍 Can't find the workflow run?** Check GitHub Actions tab manually - sometimes it takes 30-60 seconds to appear!


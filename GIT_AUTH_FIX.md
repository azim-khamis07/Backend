# Git Authentication Fix

## 🔐 Authentication Error

You encountered: `Permission denied to azim-khamis07/Backend.git`

This happens when Git doesn't have the right credentials to push to GitHub.

---

## ✅ Solutions

### Option 1: Use SSH (Recommended)

**Step 1: Check if you have SSH keys**

```bash
ls -la ~/.ssh/id_*.pub
```

If you see `id_rsa.pub` or `id_ed25519.pub`, you have SSH keys.

**Step 2: Add SSH key to GitHub**

```bash
# Copy your SSH public key
cat ~/.ssh/id_ed25519.pub
# OR
cat ~/.ssh/id_rsa.pub

# Copy the output and add to GitHub:
# GitHub → Settings → SSH and GPG keys → New SSH key
```

**Step 3: Change remote to SSH**

```bash
cd /home/azim/python-projects/Backend

# Get current remote URL
git remote get-url origin

# Change to SSH (replace YOUR_USERNAME if different)
git remote set-url origin git@github.com:azim-khamis07/Backend.git

# Verify
git remote -v

# Now try pushing again
git push origin test-ci
```

---

### Option 2: Use Personal Access Token (PAT)

**Step 1: Create GitHub Personal Access Token**

1. Go to: **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. Name: `Backend Repo Access`
4. Select scopes: `repo` (full control of private repositories)
5. Click **"Generate token"**
6. **COPY THE TOKEN** (you won't see it again!)

**Step 2: Use token to push**

```bash
cd /home/azim/python-projects/Backend

# When prompted for password, paste the token instead
git push origin test-ci

# Username: azim-khamis07
# Password: <paste your token here>
```

**Step 3: Save credentials (optional)**

```bash
# Configure Git credential helper
git config --global credential.helper store

# Push again (enter token once)
git push origin test-ci

# Token will be saved for future use
```

---

### Option 3: Use GitHub CLI (gh)

**Step 1: Install GitHub CLI (if not installed)**

```bash
# Check if installed
which gh

# If not installed:
# Ubuntu/Debian:
sudo apt install gh

# Or download from: https://cli.github.com/
```

**Step 2: Authenticate**

```bash
gh auth login

# Follow prompts:
# - GitHub.com
# - HTTPS (or SSH)
# - Authenticate Git with your GitHub credentials
# - Login with web browser (or token)
```

**Step 3: Push**

```bash
cd /home/azim/python-projects/Backend
git push origin test-ci
```

---

## 🚀 Quick Fix (Try This First)

If you have SSH keys set up, just change the remote:

```bash
cd /home/azim/python-projects/Backend

# Change to SSH
git remote set-url origin git@github.com:azim-khamis07/Backend.git

# Verify
git remote -v

# Push
git push origin test-ci
```

---

## ✅ Verify Authentication

After fixing, verify:

```bash
# Test SSH connection (if using SSH)
ssh -T git@github.com

# Should return: "Hi azim-khamis07! You've successfully authenticated..."

# Or test HTTPS with token
git ls-remote origin

# Should show remote branches without errors
```

---

## 📝 After Authentication Works

Once you can push, the CI pipeline will automatically run:

1. Push your branch: `git push origin test-ci`
2. Go to: **GitHub → Actions**
3. You'll see the CI workflow running
4. Monitor the jobs (lint, test, build)

---

## 🆘 Still Having Issues?

**Common Issues:**

1. **"Permission denied"** → Use SSH or PAT (token)
2. **"Repository not found"** → Check repository name and access
3. **"Authentication failed"** → Regenerate token or check SSH key

**Check Current Setup:**

```bash
# Remote URL
git remote -v

# Git config
git config --list | grep -E "user\.|credential|remote"

# SSH keys
ls -la ~/.ssh/

# Test SSH
ssh -T git@github.com
```

---

## 🎯 Next Steps

After fixing authentication:

1. ✅ Push the test commit: `git push origin test-ci`
2. ✅ Monitor CI: **GitHub → Actions → CI workflow**
3. ✅ Wait for jobs to complete (~10-15 minutes)
4. ✅ Verify all checks pass

---

**Need help?** Check GitHub documentation on authentication methods.


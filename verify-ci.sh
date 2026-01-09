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
echo "📤 Checking if branch exists on GitHub..."
BRANCH=$(git branch --show-current)
if git ls-remote --heads origin "$BRANCH" | grep -q .; then
    echo "✅ Branch '$BRANCH' exists on GitHub"
else
    echo "⚠️  Branch '$BRANCH' not found on GitHub"
fi

# Check workflow triggers
echo ""
echo "🔧 Workflow triggers:"
grep -A 5 "^on:" .github/workflows/ci.yml | head -8

echo ""
echo "✅ Verification complete!"
echo ""
echo "🌐 Check workflow status at:"
echo "   https://github.com/azim-khamis07/Backend/actions"
echo ""
echo "💡 Look for a workflow run with commit message 'Test CI pipeline'"

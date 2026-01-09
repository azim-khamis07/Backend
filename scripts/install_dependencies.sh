#!/bin/bash
# Dependency installation script for expense-tracker-backend

set -e

echo "========================================="
echo "Installing Dependencies"
echo "========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python 3.11+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version: $(python3 --version)"

# Check for uv (fast Python package manager)
if command -v uv &> /dev/null; then
    echo "✓ Using uv for package management"
    USE_UV=true
else
    echo "⚠ Using pip for package management"
    USE_UV=false
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    if [ "$USE_UV" = true ]; then
        uv venv
    else
        python3 -m venv venv
    fi
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip/uv
if [ "$USE_UV" = true ]; then
    uv pip install --upgrade pip
else
    pip install --upgrade pip setuptools wheel
fi

echo ""
echo "Installing project dependencies..."

# Install project in editable mode with dev dependencies
if [ "$USE_UV" = true ]; then
    uv pip install -e ".[dev]"
else
    pip install -e ".[dev]"
fi

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To check for outdated dependencies:"
echo "  python scripts/check_dependencies.py"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""


#!/bin/bash
set -e

echo "Setting up development environment for Containerlab Homelab Tools..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install production dependencies
echo "Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Run initial tests to verify setup
echo "Running initial tests..."
pytest tests/ -v --tb=short

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To install the CLI system-wide:"
echo "  ./install-cli.sh"
echo ""
echo "Common development commands:"
echo "  pytest tests/ -v                 # Run tests"
echo "  pytest tests/ --cov=clab_tools   # Run tests with coverage"
echo "  black clab_tools/ tests/         # Format code"
echo "  flake8 clab_tools/ tests/        # Lint code"
echo "  pre-commit run --all-files       # Run all pre-commit hooks"

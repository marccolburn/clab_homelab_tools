#!/bin/bash
# Script to automatically fix common flake8 issues

echo "🔧 Fixing common flake8 issues automatically..."

echo "  ▶ Running autoflake to remove unused imports..."
python -m autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive clab_tools/ main.py tests/

echo "  ▶ Running black to fix line length issues..."
python -m black --line-length 88 clab_tools/ main.py tests/

echo "  ▶ Running isort to organize imports..."
python -m isort --profile black clab_tools/ main.py tests/

echo "✅ Automatic fixes completed!"
echo "📋 Run 'flake8' to see remaining issues that need manual fixing."

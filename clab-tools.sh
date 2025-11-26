#!/bin/bash

# Containerlab Homelab Tools - System-wide CLI wrapper
# This script provides a convenient wrapper for the main.py CLI utility
# that can be executed from anywhere on the system as 'clab-tools'.

# Determine the actual script directory (resolve symlinks)
# This ensures we find the real script location even when called via symlink
SCRIPT_PATH="${BASH_SOURCE[0]}"
# Resolve symlinks to get the actual script path
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON_CMD" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Resolved script directory: $SCRIPT_DIR"
    echo "Looking for Python at: $PYTHON_CMD"
    echo ""
    echo "Please run the following commands in $SCRIPT_DIR:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Check if package is installed
if ! "$PYTHON_CMD" -c "import clab_tools" 2>/dev/null; then
    echo "Error: clab_tools package not installed in virtual environment"
    echo "Resolved script directory: $SCRIPT_DIR"
    echo ""
    echo "Please run the following commands in $SCRIPT_DIR:"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Run as Python module (handles package imports correctly)
exec "$PYTHON_CMD" -m clab_tools.cli "$@"

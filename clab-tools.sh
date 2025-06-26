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
MAIN_SCRIPT="$SCRIPT_DIR/clab_tools/main.py"

# Check if virtual environment exists
if [ ! -f "$PYTHON_CMD" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Resolved script directory: $SCRIPT_DIR"
    echo "Looking for Python at: $PYTHON_CMD"
    echo ""
    echo "Please run the following commands in $SCRIPT_DIR:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if main.py exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: main.py not found at $MAIN_SCRIPT"
    echo "Resolved script directory: $SCRIPT_DIR"
    echo "Please ensure the clab_homelab_tools project is properly installed."
    exit 1
fi

# Run the Python script with all passed arguments
exec "$PYTHON_CMD" "$MAIN_SCRIPT" "$@"

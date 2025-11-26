#!/bin/bash

# Installation script for system-wide clab-tools CLI access
# Run this script to install the clab-tools command system-wide

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_SCRIPT="$SCRIPT_DIR/clab-tools.sh"
INSTALL_PATH="/usr/local/bin/clab-tools"

echo "Installing Containerlab Homelab Tools CLI..."

# Check if the CLI script exists
if [ ! -f "$CLI_SCRIPT" ]; then
    echo "Error: clab-tools.sh not found in $SCRIPT_DIR"
    exit 1
fi

# Make sure the CLI script is executable
chmod +x "$CLI_SCRIPT"

# Check if virtual environment exists
if [ ! -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run the following commands first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Check if package is installed in editable mode
if ! "$SCRIPT_DIR/.venv/bin/python" -c "import clab_tools" 2>/dev/null; then
    echo "Error: clab_tools package not installed."
    echo "Please run the following commands first:"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Create symlink (requires sudo)
echo "Creating symlink at $INSTALL_PATH (requires sudo)..."
sudo ln -sf "$CLI_SCRIPT" "$INSTALL_PATH"

# Verify installation
if [ -L "$INSTALL_PATH" ] && [ -x "$INSTALL_PATH" ]; then
    echo "✅ Installation successful!"
    echo "You can now use 'clab-tools' from anywhere on your system."
    echo ""
    echo "Try: clab-tools --help"
else
    echo "❌ Installation failed. Please check permissions and try again."
    exit 1
fi

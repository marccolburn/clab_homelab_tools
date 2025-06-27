#!/bin/bash
# Version management script for clab-tools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/../clab_tools/_version.py"

# Function to get current version
get_current_version() {
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/../')
from clab_tools._version import __version__
print(__version__)
"
}

# Function to set new version
set_version() {
    local new_version="$1"
    if [[ ! "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Version must be in format X.Y.Z (e.g., 1.0.0)"
        exit 1
    fi

    echo "Updating version to $new_version..."

    # Update _version.py
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$new_version\"/" "$VERSION_FILE"
    rm -f "$VERSION_FILE.bak"

    echo "✅ Updated $VERSION_FILE"
    echo "✅ Version updated to $new_version"
    echo ""
    echo "Next steps:"
    echo "1. Commit the version change: git add . && git commit -m 'release: version $new_version'"
    echo "2. Create a tag: git tag v$new_version"
    echo "3. Push changes: git push && git push --tags"
}

# Function to check version consistency
check_version() {
    local current_version
    current_version=$(get_current_version)

    echo "Current version: $current_version"
    echo "Checking version consistency across files..."

    # Check if there are any hardcoded versions that don't match
    local inconsistent_files=()

    # Check main.py for any hardcoded versions (should not exist now)
    if grep -q "version=\"[0-9]" "$SCRIPT_DIR/../clab_tools/main.py" 2>/dev/null; then
        inconsistent_files+=("clab_tools/main.py")
    fi

    # Check documentation for version examples
    if grep -rq "version.*[0-9]\+\.[0-9]\+\.[0-9]\+" "$SCRIPT_DIR/../docs/" 2>/dev/null; then
        echo "⚠️  Found version references in documentation - these may need manual updates"
    fi

    if [ ${#inconsistent_files[@]} -eq 0 ]; then
        echo "✅ Version consistency check passed"
    else
        echo "❌ Found inconsistent version references in:"
        printf '%s\n' "${inconsistent_files[@]}"
        exit 1
    fi
}

# Main script logic
case "${1:-}" in
    "get"|"current")
        get_current_version
        ;;
    "set")
        if [ -z "$2" ]; then
            echo "Usage: $0 set <version>"
            echo "Example: $0 set 1.0.1"
            exit 1
        fi
        set_version "$2"
        ;;
    "check")
        check_version
        ;;
    *)
        echo "clab-tools version management script"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  get, current    Show current version"
        echo "  set <version>   Update version to new value (e.g., 1.0.1)"
        echo "  check          Check version consistency across files"
        echo ""
        echo "Examples:"
        echo "  $0 get"
        echo "  $0 set 1.0.1"
        echo "  $0 check"
        exit 1
        ;;
esac

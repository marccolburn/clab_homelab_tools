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

    local current_version
    current_version=$(get_current_version)

    echo "Updating version from $current_version to $new_version..."

    # Update _version.py
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$new_version\"/" "$VERSION_FILE"
    rm -f "$VERSION_FILE.bak"
    echo "✅ Updated $VERSION_FILE"

    # Update documentation examples that use version numbers
    local docs_dir="$SCRIPT_DIR/../docs"
    if [ -d "$docs_dir" ]; then
        echo "Updating documentation examples..."

        # Update configuration.md version examples
        if [ -f "$docs_dir/configuration.md" ]; then
            # Update the example version in project configuration
            sed -i.bak "s/version: \"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"/version: \"$new_version\"/" "$docs_dir/configuration.md"

            # Update the table example - fix the escaped backticks
            sed -i.bak "s/| \`project\.version\` | Project version | \`\"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"\` |/| \`project.version\` | Project version | \`\"$new_version\"\` |/" "$docs_dir/configuration.md"

            rm -f "$docs_dir/configuration.md.bak"
            echo "✅ Updated $docs_dir/configuration.md"
        fi

        # Update development.md version examples
        if [ -f "$docs_dir/development.md" ]; then
            # Update version set examples
            sed -i.bak "s/\.\/scripts\/version\.sh set [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/\.\/scripts\/version.sh set $new_version/g" "$docs_dir/development.md"

            # Update commit message examples - be more specific to avoid changing unrelated version numbers
            sed -i.bak "s/\"release: version [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"/\"release: version $new_version\"/g" "$docs_dir/development.md"

            # Update git tag examples
            sed -i.bak "s/git tag v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/git tag v$new_version/g" "$docs_dir/development.md"

            rm -f "$docs_dir/development.md.bak"
            echo "✅ Updated $docs_dir/development.md"
        fi

        # Update any other documentation files with version examples
        # Look for common patterns in other files
        find "$docs_dir" -name "*.md" -not -name "configuration.md" -not -name "development.md" -exec grep -l "[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*" {} \; | while read -r file; do
            # Create backup
            cp "$file" "$file.bak"

            # Update generic version patterns in examples, but be conservative
            # Only update patterns that look like version examples (quoted or in code blocks)
            sed -i.tmp "s/\"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"/\"$new_version\"/g" "$file"
            sed -i.tmp "s/\`[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\`/\`$new_version\`/g" "$file"
            sed -i.tmp "s/v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/v$new_version/g" "$file"

            # Check if file actually changed
            if ! cmp -s "$file" "$file.bak"; then
                echo "✅ Updated $(basename "$file")"
                rm -f "$file.bak" "$file.tmp"
            else
                # Restore original if no changes
                mv "$file.bak" "$file"
                rm -f "$file.tmp"
            fi
        done

        echo "✅ Updated documentation examples"
    fi

    echo "✅ Version updated to $new_version"
    echo ""
    echo "Files updated:"
    echo "  - clab_tools/_version.py"
    echo "  - docs/configuration.md (version examples)"
    echo "  - docs/development.md (version examples)"
    echo "  - docs/*.md (other version examples as found)"
    echo ""
    echo "Next steps:"
    echo "1. Review changes: git diff"
    echo "2. Commit the version change: git add . && git commit -m 'release: version $new_version'"
    echo "3. Create a tag: git tag v$new_version"
    echo "4. Push changes: git push && git push --tags"
}

# Function to check version consistency
check_version() {
    local current_version
    current_version=$(get_current_version)

    echo "Current version: $current_version"
    echo "Checking version consistency across files..."

    local inconsistent_files=()
    local docs_issues=()

    # Check main.py for any hardcoded versions (should not exist now)
    if grep -q "version=\"[0-9]" "$SCRIPT_DIR/../clab_tools/main.py" 2>/dev/null; then
        inconsistent_files+=("clab_tools/main.py")
    fi

    # Check if pyproject.toml correctly references the version module
    if ! grep -q 'version = {attr = "clab_tools.__version__"}' "$SCRIPT_DIR/../pyproject.toml" 2>/dev/null; then
        inconsistent_files+=("pyproject.toml (should use dynamic version)")
    fi

    # Check documentation for outdated version examples
    local docs_dir="$SCRIPT_DIR/../docs"
    if [ -d "$docs_dir" ]; then
        # Check for version numbers that don't match current version
        while IFS= read -r line; do
            if [[ "$line" != *"$current_version"* ]]; then
                docs_issues+=("$line")
            fi
        done < <(grep -rn "version.*[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*" "$docs_dir/" 2>/dev/null || true)
    fi

    # Report results
    echo ""
    echo "📋 Version Check Results:"
    echo "========================"

    if [ ${#inconsistent_files[@]} -eq 0 ]; then
        echo "✅ Core version consistency check passed"
    else
        echo "❌ Found inconsistent version references in:"
        printf '  - %s\n' "${inconsistent_files[@]}"
    fi

    if [ ${#docs_issues[@]} -eq 0 ]; then
        echo "✅ Documentation version examples are up to date"
    else
        echo "⚠️  Found potentially outdated version examples in documentation:"
        printf '  - %s\n' "${docs_issues[@]}"
        echo ""
        echo "💡 Run './scripts/version.sh set $current_version' to update documentation examples"
    fi

    echo ""
    echo "📍 Version Sources:"
    echo "  - Single source of truth: clab_tools/_version.py"
    echo "  - Dynamic import in: pyproject.toml"
    echo "  - Documentation examples: docs/ (auto-updated by version script)"

    if [ ${#inconsistent_files[@]} -ne 0 ]; then
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
    "update-docs")
        # Update documentation to match current version without changing the version
        current_version=$(get_current_version)
        echo "Updating documentation examples to match current version ($current_version)..."

        # Update documentation examples that use version numbers
        docs_dir="$SCRIPT_DIR/../docs"
        if [ -d "$docs_dir" ]; then
            echo "Updating documentation examples..."

            # Update configuration.md version examples
            if [ -f "$docs_dir/configuration.md" ]; then
                # Update the example version in project configuration
                sed -i.bak "s/version: \"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"/version: \"$current_version\"/" "$docs_dir/configuration.md"

                # Update the table example - fix the escaped backticks
                sed -i.bak "s/| \`project\.version\` | Project version | \`\"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"\` |/| \`project.version\` | Project version | \`\"$current_version\"\` |/" "$docs_dir/configuration.md"

                rm -f "$docs_dir/configuration.md.bak"
                echo "✅ Updated $docs_dir/configuration.md"
            fi

            # Update development.md version examples
            if [ -f "$docs_dir/development.md" ]; then
                # Update version set examples
                sed -i.bak "s/\.\/scripts\/version\.sh set [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/\.\/scripts\/version.sh set $current_version/g" "$docs_dir/development.md"

                # Update commit message examples - be more specific to avoid changing unrelated version numbers
                sed -i.bak "s/\"release: version [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"/\"release: version $current_version\"/g" "$docs_dir/development.md"

                # Update git tag examples
                sed -i.bak "s/git tag v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/git tag v$current_version/g" "$docs_dir/development.md"

                rm -f "$docs_dir/development.md.bak"
                echo "✅ Updated $docs_dir/development.md"
            fi

            # Update any other documentation files with version examples
            # Look for common patterns in other files
            find "$docs_dir" -name "*.md" -not -name "configuration.md" -not -name "development.md" -exec grep -l "[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*" {} \; | while read -r file; do
                # Create backup
                cp "$file" "$file.bak"

                # Update generic version patterns in examples, but be conservative
                # Only update patterns that look like version examples (quoted or in code blocks)
                sed -i.tmp "s/\"[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\"/\"$current_version\"/g" "$file"
                sed -i.tmp "s/\`[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\`/\`$current_version\`/g" "$file"
                sed -i.tmp "s/v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/v$current_version/g" "$file"

                # Check if file actually changed
                if ! cmp -s "$file" "$file.bak"; then
                    echo "✅ Updated $(basename "$file")"
                    rm -f "$file.bak" "$file.tmp"
                else
                    # Restore original if no changes
                    mv "$file.bak" "$file"
                    rm -f "$file.tmp"
                fi
            done

            echo "✅ Updated documentation examples to version $current_version"
        fi
        ;;
    *)
        echo "clab-tools version management script"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  get, current      Show current version"
        echo "  set <version>     Update version to new value (e.g., 1.0.1)"
        echo "  check            Check version consistency across files"
        echo "  update-docs      Update documentation examples to match current version"
        echo ""
        echo "Examples:"
        echo "  $0 get"
        echo "  $0 set 1.0.1"
        echo "  $0 check"
        echo "  $0 update-docs"
        exit 1
        ;;
esac

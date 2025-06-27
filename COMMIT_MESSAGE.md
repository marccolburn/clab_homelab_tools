feat: major refactor - streamline documentation, centralize version management, and prepare v1.0.0 release

## 📚 Documentation Overhaul
- **Eliminated redundancy**: Removed 13 overlapping documentation files (5,663 lines removed)
- **Streamlined structure**: Replaced massive docs with 8 focused guides
- **Improved navigation**: README.md now serves as clear documentation index
- **Enhanced readability**: Workflow-oriented approach with practical examples

### New Documentation Structure:
- `docs/getting-started.md` - Installation and first steps
- `docs/user-guide.md` - Complete workflow guide with examples
- `docs/commands.md` - CLI command reference
- `docs/configuration.md` - Settings and customization
- `docs/csv-format.md` - Data format specifications
- `docs/remote-setup.md` - Remote host configuration
- `docs/development.md` - Contributing and development setup
- `docs/troubleshooting.md` - Problem resolution guide

### Removed Redundant Files:
- `docs/installation.md` → merged into `getting-started.md`
- `docs/developer-guide.md` + `development-workflow.md` → consolidated into `development.md`
- `docs/architecture.md` + `workflows-and-architecture.md` → key parts moved to `README.md`
- `docs/remote-host-management.md` → consolidated into `remote-setup.md`
- `docs/api-reference.md` + `configuration-override-patterns.md` → merged into `configuration.md`
- `docs/simplified-bridge-guide.md` → content moved to `user-guide.md`
- `QUICK_REFERENCE.md` → replaced by `commands.md`

## 🔧 Version Management System
- **Centralized versioning**: Created `clab_tools/_version.py` as single source of truth
- **Dynamic packaging**: Updated `pyproject.toml` to use dynamic version from code
- **CLI version support**: Added `--version` option to CLI
- **Version management script**: Created `scripts/version.sh` for easy version updates
- **Consistent imports**: All files now import version from central location

### Version Management Features:
```bash
./scripts/version.sh get      # Get current version
./scripts/version.sh set 1.1.0  # Update version
./scripts/version.sh check    # Check consistency
```

## 🧹 Repository Cleanup
- **Removed build artifacts**: Cleaned up `.coverage`, `htmlcov/`, `*.egg-info/`
- **Eliminated duplicates**: Removed redundant `config.example.yaml`
- **Removed generated files**: Cleaned up `clab.yml` and development database
- **Improved .gitignore**: Added proper exclusions for build artifacts

## 🏗️ Code Improvements
- **Fixed SQLAlchemy relationships**: Resolved model relationship errors using `foreign()` annotations
- **Enhanced database models**: Improved SQLAlchemy models with better relationships and constraints
- **Better error handling**: Consistent error handling across CLI commands
- **Improved test coverage**: Updated test fixtures and added integration tests
- **Configuration enhancements**: Better settings management and validation
- **CLI improvements**: More consistent command structure and help text

## 📦 Release Preparation
- **Version 1.0.0**: Prepared for stable release
- **Semantic versioning**: Implemented proper version management
- **Release process**: Documented in development guide
- **Backward compatibility**: Maintained CLI interface compatibility

## 📊 Impact Summary
- **Lines of code**: Net reduction of 4,281 lines (removed redundancy)
- **Documentation**: 8 focused docs vs 21 overlapping files
- **Maintainability**: Single source of truth for version and configuration
- **User experience**: Clear navigation and workflow-oriented documentation
- **Developer experience**: Streamlined development setup and release process

## 🔄 Breaking Changes
- None - all CLI commands and functionality remain compatible
- Documentation reorganization does not affect code behavior
- Configuration file format unchanged

## ✅ Testing
- All existing tests pass with updated fixtures
- CLI commands verified to work correctly
- Version management system tested
- Documentation links verified

This refactor significantly improves maintainability, reduces redundancy, and prepares the project for stable v1.0.0 release while maintaining full backward compatibility.

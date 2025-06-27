# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Setup development environment with virtual environment and dependencies
./scripts/setup-dev.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Testing
```bash
# Run all tests with verbose output and coverage
python -m pytest tests/ -v --cov=clab_tools --cov-report=html

# Run specific test file
python -m pytest tests/test_database.py -v

# Run single test
python -m pytest tests/test_database.py::TestDatabaseManager::test_create_node -v
```

### Linting and Formatting
```bash
# Auto-fix common issues (removes unused imports, formats code, organizes imports)
./scripts/fix-lint.sh

# Or manually:
python -m black --line-length 88 clab_tools/ tests/
python -m isort --profile black clab_tools/ tests/
python -m flake8 clab_tools/ tests/

# Type checking
python -m mypy clab_tools/
```

### Version Management
```bash
# Check current version
./scripts/version.sh get

# Update version (centralized in clab_tools/_version.py)
./scripts/version.sh set 1.0.1

# Verify version consistency
./scripts/version.sh check
```

### CLI Installation
```bash
# Install the clab-tools CLI
./install-cli.sh

# Run CLI commands
clab-tools --help
```

## Architecture

This is a multi-lab containerlab management tool with the following key components:

### Core Components
- **Multi-Lab Database**: SQLite database with lab isolation using SQLAlchemy ORM (models in `clab_tools/db/models.py`)
- **Command Structure**: Click-based CLI with modular commands in `clab_tools/commands/`
- **Common Utilities**: Shared helpers for UI consistency (`handle_success`, `handle_error`, `with_lab_context`)
- **Remote Host Support**: SSH-based remote containerlab host management for deployment
- **Bridge Management**: Linux bridge creation and VLAN configuration for network connectivity
- **Topology Generation**: Jinja2-based YAML generation from database entries

### Key Design Patterns
1. **Lab-Aware Database**: DatabaseManager is inherently lab-aware, eliminating need for wrapper classes
2. **Common Utilities**: Shared utilities in `clab_tools/common/utils.py` for consistent UI patterns
3. **Settings Management**: Hierarchical configuration (YAML files → env vars → CLI args) via Pydantic
4. **Error Handling**: Centralized error handling with custom exceptions and decorators
5. **Logging**: Structured logging with configurable levels and formats

### Command Flow
1. User selects/creates a lab (stored in settings)
2. DatabaseManager initialized with current lab context
3. Commands use simplified context access via `get_lab_db(ctx.obj)`
4. Data can be imported from CSV files (nodes.csv, connections.csv)
5. Topology YAML is generated from database data
6. Bridges are created locally or on remote hosts
7. Containerlab deployment happens via local/remote execution

### Database Schema
The SQLite database uses separate tables per lab with prefixes:
- `{lab_name}_nodes`: Network devices/containers
- `{lab_name}_connections`: Network links between nodes
- `{lab_name}_vlans`: VLAN configurations
- `{lab_name}_interfaces`: Interface details

### Remote Operations
Remote functionality uses SSH (paramiko) to:
- Test connectivity to containerlab hosts
- Upload topology files
- Execute containerlab commands
- Create bridges on remote systems

## Testing Strategy

The codebase includes comprehensive tests:
- Unit tests for all core components
- Integration tests for database operations
- Mock-based tests for remote operations
- Fixture-based testing with pytest

When adding new features:
1. Add unit tests in corresponding test files
2. Use existing fixtures from `conftest.py`
3. Mock external dependencies (SSH, filesystem)
4. Ensure tests are isolated and repeatable

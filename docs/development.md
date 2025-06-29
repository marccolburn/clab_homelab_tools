# Development Guide

Contributing to and developing clab-tools.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools
./scripts/setup-dev.sh

# Activate and test
source .venv/bin/activate
python -m pytest tests/ -v

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 2. Code Changes

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
python -m pytest tests/ -v
./scripts/fix-lint.sh

# Run full test suite
python -m pytest tests/ --cov=clab_tools --cov-report=html
```

### 3. Submit Changes

```bash
# Format and lint
black clab_tools/ tests/
flake8 clab_tools/ tests/
mypy clab_tools/

# Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

## Project Architecture

```
clab_tools/
├── commands/          # CLI command implementations
├── db/               # SQLite database models
├── config/           # Configuration management
├── bridges/          # Bridge management
├── topology/         # Topology generation
├── node/             # Node management (SSH/upload)
├── remote/           # Remote host operations
├── log_config/       # Logging setup
├── common/           # Common utilities
└── errors/           # Custom exceptions
```

## Testing

### Running Tests

```bash
# All tests with verbose output
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_database.py -v

# With coverage report
python -m pytest tests/ --cov=clab_tools --cov-report=html

# Remote integration tests (requires containerlab)
python -m pytest tests/test_remote_*.py -v
```

### Test Structure

All tests are located in the `tests/` directory as individual test files:

```
tests/
├── conftest.py                      # Pytest fixtures and configuration
├── test_database.py                 # Database operations
├── test_bridge_manager.py           # Bridge management
├── test_topology_generator.py       # Topology generation
├── test_csv_import.py               # CSV import functionality
├── test_config*.py                  # Configuration tests
├── test_quiet_mode.py               # Non-interactive mode tests
├── test_start_stop_commands.py      # Topology lifecycle tests
├── test_node_upload.py              # Node file upload tests
├── test_bootstrap_teardown.py       # Lab lifecycle tests
└── test_remote_*.py                 # Remote operation tests
```

## Code Guidelines

### Style and Quality

- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking
- **isort** for import sorting
- **Important**: All imports must be at the top of the file (never inside functions)

```bash
# Format code
black clab_tools/ tests/
isort clab_tools/ tests/

# Check style
flake8 clab_tools/ tests/
mypy clab_tools/
```

### Adding New Commands

1. Create module in `clab_tools/commands/`
2. Use Click decorators for CLI integration
3. Add proper error handling and logging
4. Include docstrings and type hints
5. Add unit tests

```python
# clab_tools/commands/example.py
import click
from clab_tools.db.context import get_lab_db
from clab_tools.logging import get_logger

logger = get_logger(__name__)

@click.command()
@click.option("--name", required=True, help="Resource name")
@click.pass_context
def create_resource(ctx, name: str) -> None:
    """Create a new resource."""
    try:
        lab_db = get_lab_db(ctx.obj)
        # Implementation
        logger.info(f"Created resource: {name}")
    except Exception as e:
        logger.error(f"Failed to create resource: {e}")
        raise click.ClickException(str(e))
```

### Database Changes

1. Update models in `clab_tools/db/models.py`
2. Create migration script if needed
3. Update database manager methods
4. Add tests for new functionality

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch from `main`
3. Make changes with tests
4. Ensure all checks pass
5. Submit PR with clear description

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No breaking changes without version bump
- [ ] Error handling implemented
- [ ] Logging added for important operations

## Development Tools

### Available Scripts

```bash
./scripts/setup-dev.sh      # Setup development environment
./scripts/fix-lint.sh       # Auto-fix linting issues
./scripts/version.sh        # Manage project version
```

### Version Management

The project uses centralized version management:

```bash
# Check current version
./scripts/version.sh get

# Update version (follows semantic versioning)
./scripts/version.sh set 1.1.0

# Check version consistency
./scripts/version.sh check
```

**Version update process:**
1. Update version: `./scripts/version.sh set 1.1.0`
2. Commit changes: `git add . && git commit -m "release: version 1.1.0"`
3. Create tag: `git tag v1.1.0`
4. Push: `git push && git push --tags`

### IDE Configuration

#### VS Code

Recommended extensions:
- Python
- Black Formatter
- Flake8
- MyPy Type Checker

#### Settings

```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true
}
```

## Debugging

### Common Issues

```bash
# Import errors
pip install -e .

# Database issues (removes database from project directory)
rm clab_topology.db
clab-tools data show  # Will recreate database automatically

# Permission errors (bridges)
sudo ./clab-tools.sh bridge create br-test
```

### Logging

Enable debug logging:

```bash
export CLAB_LOG_LEVEL=DEBUG
./clab-tools.sh --verbose command
```

./clab-tools.sh --debug --enable-remote remote test-connection
```

## Contributing Guidelines

### Pull Request Process

1. **Fork repository** and create feature branch
2. **Make changes** with appropriate tests
3. **Run test suite** and ensure all pass
4. **Update documentation** if needed
5. **Submit pull request** with clear description

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints for all functions
- Write docstrings for modules, classes, and functions
- Include tests for new functionality
- Update documentation for user-facing changes

### Commit Messages

Use conventional commit format:
```
feat: add new bridge configuration option
fix: resolve remote connection timeout
docs: update installation guide
test: add integration tests for lab management
```

## Release Process

### Version Bump

```bash
# Update version in setup.py and __init__.py
# Create release commit
git commit -m "release: version 1.1.0"
git tag v1.1.0

# Push release
git push origin main --tags
```

### Testing Release

```bash
# Test installation from source
pip install .

# Test CLI installation
./install-cli.sh
clab-tools --version
```

## Troubleshooting Development

### Common Issues

**Import Errors:**
```bash
# Ensure package is installed in development mode
pip install -e .
```

**Test Failures:**
```bash
# Clean up test databases
rm -f tests/test_*.db

# Refresh test environment
./scripts/setup-dev.sh
```

**CLI Not Working:**
```bash
# Check installation
which clab-tools
cat ~/.local/bin/clab-tools

# Reinstall CLI
./install-cli.sh
```

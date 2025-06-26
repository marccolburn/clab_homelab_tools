# Developer Guide

Guide for developers working on the Containerlab Homelab Tools project.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Text editor or IDE (VS Code recommended)

### Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd clab_homelab_tools

# Create development environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
python -m pytest tests/ -v
```

## Project Structure

```
clab_homelab_tools/
├── main.py                     # CLI entry point
├── requirements.txt            # Dependencies
├── pytest.ini                  # Test configuration
├── config.yaml                 # Sample configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Project overview
├── QUICK_REFERENCE.md          # Command summary
├── docs/                       # Documentation
│   ├── installation.md
│   ├── user-guide.md
│   ├── developer-guide.md
│   ├── configuration.md
│   ├── architecture.md
│   ├── troubleshooting.md
│   └── api-reference.md
├── clab_tools/                 # Main package
│   ├── __init__.py
│   ├── config/                 # Configuration system
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── logging/                # Logging system
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── errors/                 # Error handling
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   └── handlers.py
│   ├── db/                     # Database layer
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── manager.py
│   ├── topology/               # Topology generation
│   │   ├── __init__.py
│   │   └── generator.py
│   ├── bridges/                # Bridge management
│   │   ├── __init__.py
│   │   └── manager.py
│   └── commands/               # CLI commands
│       ├── __init__.py
│       ├── import_csv.py
│       ├── generate_topology.py
│       ├── bridge_commands.py
│       └── data_commands.py
├── tests/                      # Test suite
│   ├── conftest.py             # Test fixtures
│   ├── test_database.py
│   ├── test_config.py
│   └── test_csv_import.py
├── example_nodes.csv           # Sample data
├── example_connections.csv     # Sample data
├── topology_template.j2        # Jinja2 template
├── supported_kinds.yaml        # Device types
└── clab-tools.sh               # System-wide CLI wrapper
```

## Development Workflow

### 1. Code Changes

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes to code
# Edit files in clab_tools/

# Test changes
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=clab_tools --cov-report=term-missing
```

### 2. Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_database.py -v

# Run specific test class
python -m pytest tests/test_database.py::TestDatabaseManager -v

# Run specific test function
python -m pytest tests/test_database.py::TestDatabaseManager::test_insert_node -v

# Run with coverage report
python -m pytest tests/ --cov=clab_tools --cov-report=html
# Open htmlcov/index.html in browser
```

### 3. Code Quality

#### Type Checking (Optional)
```bash
# Install mypy
pip install mypy

# Run type checking
mypy clab_tools/
```

#### Code Formatting (Optional)
```bash
# Install formatting tools
pip install black isort

# Format code
black clab_tools/ tests/

# Sort imports
isort clab_tools/ tests/
```

### 4. Debugging

```bash
# Enable debug logging
python main.py --debug --log-level DEBUG show-data

# Database debugging (set in config.yaml)
database:
  echo: true  # Enables SQL query logging

# Function call tracing (automatic in debug mode)
python main.py --debug import-csv -n nodes.csv -c connections.csv
```

## Architecture Overview

### Core Principles

1. **Modular Design**: Separate concerns into focused modules
2. **Type Safety**: Use type hints throughout the codebase
3. **Error Handling**: Comprehensive error handling with context
4. **Testing**: High test coverage with integration tests
5. **Logging**: Structured logging for observability
6. **Configuration**: Flexible configuration management

### Module Responsibilities

#### Configuration (`clab_tools/config/`)
- Pydantic-based settings management
- Environment variable support
- Configuration file parsing

#### Logging (`clab_tools/logging/`)
- Structlog integration
- Rich console output
- File logging with rotation

#### Errors (`clab_tools/errors/`)
- Custom exception classes
- Error handling decorators
- Context management

#### Database (`clab_tools/db/`)
- SQLAlchemy ORM models
- Database connection management
- Health checks and connection pooling

#### Topology (`clab_tools/topology/`)
- Jinja2 template processing
- YAML generation
- Validation

#### Bridges (`clab_tools/bridges/`)
- Linux bridge management
- System integration
- Dry-run functionality

#### Commands (`clab_tools/commands/`)
- CLI command implementations
- Input validation
- Business logic orchestration

## Testing Framework

### Test Organization

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test end-to-end workflows
- **Fixtures**: Reusable test data and database instances
- **Mocking**: External dependency simulation

### Test Configuration

`pytest.ini`:
```ini
[pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Writing Tests

#### Unit Test Example
```python
def test_node_creation():
    """Test creating a node with valid data."""
    node = Node(name="test_node", kind="test_kind", mgmt_ip="10.0.0.1")
    assert node.name == "test_node"
    assert node.kind == "test_kind"
    assert node.mgmt_ip == "10.0.0.1"
```

#### Integration Test Example
```python
def test_csv_import_workflow(db_manager, sample_csv_files):
    """Test complete CSV import workflow."""
    # Import CSV data
    import_csv_command(sample_csv_files.nodes, sample_csv_files.connections)

    # Verify data was imported
    nodes = db_manager.get_all_nodes()
    assert len(nodes) == 3

    connections = db_manager.get_all_connections()
    assert len(connections) == 2
```

### Test Fixtures

Located in `tests/conftest.py`:

```python
@pytest.fixture
def db_manager():
    """Provide a clean database manager for testing."""
    # Setup code
    yield manager
    # Cleanup code

@pytest.fixture
def sample_csv_files():
    """Provide sample CSV files for testing."""
    # Create temporary CSV files
    yield csv_files
    # Cleanup files
```

## Adding New Features

### 1. New CLI Command

```bash
# Create command file
touch clab_tools/commands/my_command.py
```

```python
# clab_tools/commands/my_command.py
import click
from clab_tools.logging import get_logger

logger = get_logger(__name__)

@click.command()
@click.option('--param', help='Command parameter')
def my_command(param: str):
    """My new command description."""
    logger.info("Executing my command", param=param)
    # Implementation here
```

```python
# main.py - Register the command
from clab_tools.commands.my_command import my_command
cli.add_command(my_command)
```

### 2. New Database Model

```python
# clab_tools/db/models.py
from sqlalchemy.orm import Mapped, mapped_column

class MyModel(Base):
    __tablename__ = 'my_table'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
```

### 3. New Configuration Option

```python
# clab_tools/config/settings.py
class MyModuleSettings(BaseModel):
    new_option: str = "default_value"

class Settings(BaseSettings):
    my_module: MyModuleSettings = MyModuleSettings()
```

### 4. Add Tests

```python
# tests/test_my_feature.py
import pytest
from clab_tools.my_module import MyClass

class TestMyFeature:
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = MyClass().do_something()
        assert result == expected_value
```

## Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all functions and class methods
- Add docstrings for all public functions and classes
- Use descriptive variable and function names

### Example:
```python
from typing import List, Optional
from clab_tools.logging import get_logger

logger = get_logger(__name__)

class MyClass:
    """Example class with proper style."""

    def __init__(self, name: str) -> None:
        """Initialize the class.

        Args:
            name: The name to use
        """
        self.name = name
        logger.debug("Initialized MyClass", name=name)

    def process_items(self, items: List[str]) -> Optional[str]:
        """Process a list of items.

        Args:
            items: List of items to process

        Returns:
            Processed result or None if no items

        Raises:
            ValueError: If items list is invalid
        """
        if not items:
            return None

        logger.info("Processing items", count=len(items))
        # Implementation here
        return result
```

### Error Handling

```python
from clab_tools.errors import ClabToolsError, DatabaseError

def my_function() -> str:
    """Example function with proper error handling."""
    try:
        # Some operation
        result = risky_operation()
        return result
    except SpecificError as e:
        logger.error("Specific error occurred", error=str(e))
        raise DatabaseError(f"Database operation failed: {e}") from e
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        raise ClabToolsError(f"Unexpected error: {e}") from e
```

## Debugging Tips

### 1. Enable Debug Logging

```bash
# Global debug mode
python main.py --debug show-data

# Specific log level
python main.py --log-level DEBUG show-data

# JSON logging for parsing
python main.py --log-format json --log-level DEBUG show-data
```

### 2. Database Debugging

```yaml
# config.yaml - Enable SQL query logging
database:
  echo: true
```

### 3. Function Tracing

Debug mode automatically enables function call tracing:
- Function entry/exit
- Arguments and return values
- Execution timing
- Error context

### 4. Interactive Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()
```

## Performance Considerations

### Database Operations
- Use bulk operations for large datasets
- Implement proper indexing
- Monitor query performance with `echo: true`

### Memory Usage
- Process large CSV files in chunks
- Use generators for data streaming
- Monitor memory usage during testing

### Logging Performance
- Use appropriate log levels
- Avoid expensive operations in log messages
- Use structured logging for better performance

## Contributing Guidelines

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes**
   - Follow code style guidelines
   - Add appropriate tests
   - Update documentation

3. **Test Changes**
   ```bash
   python -m pytest tests/ --cov=clab_tools
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/my-feature
   # Create pull request on GitHub
   ```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Test coverage maintained (85%+)
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Logging added where appropriate
- [ ] Type hints included
- [ ] No breaking changes (or documented)

### Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Create release branch
5. Tag release
6. Update documentation

## Advanced Topics

### Custom Error Types

```python
# clab_tools/errors/exceptions.py
class MyCustomError(ClabToolsError):
    """Custom error for specific functionality."""
    pass
```

### Configuration Extensions

```python
# clab_tools/config/settings.py
class AdvancedSettings(BaseModel):
    """Advanced configuration options."""
    feature_enabled: bool = False
    max_retries: int = 3
    timeout: float = 30.0
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head
```

### Custom Templates

Create custom Jinja2 templates for topology generation:

```jinja2
{# custom_template.j2 #}
name: {{ topology_name }}
prefix: {{ prefix }}

topology:
  nodes:
  {% for node in nodes %}
    {{ node.name }}:
      kind: {{ node.kind }}
      # Custom node configuration
  {% endfor %}
```

For more information, see:
- [Architecture Documentation](architecture.md)
- [API Reference](api-reference.md)
- [Troubleshooting Guide](troubleshooting.md)

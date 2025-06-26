# Architecture Guide

Detailed architectural overview of the Containerlab Homelab Tools.

## Overview

The Containerlab Homelab Tools represents a complete architectural transformation from a simple script to an enterprise-ready application with modern Python best practices.

## Design Principles

### 1. Modular Architecture
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Loose Coupling**: Modules interact through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 2. Modern Python Practices
- **Type Safety**: Full type hints throughout the codebase
- **Configuration Management**: Pydantic-based settings with validation
- **Structured Logging**: Contextual, searchable logs
- **Error Handling**: Comprehensive error management with context

### 3. Enterprise Readiness
- **Observability**: Detailed logging and monitoring capabilities
- **Reliability**: Robust error handling and recovery
- **Scalability**: Connection pooling and efficient resource management
- **Maintainability**: Clear structure and comprehensive testing

## Module Architecture

```
clab_tools/
├── __init__.py                 # Package initialization
├── config/                     # Configuration Management
│   ├── __init__.py
│   └── settings.py             # Pydantic settings with validation
├── logging/                    # Structured Logging
│   ├── __init__.py
│   └── logger.py               # Structlog configuration
├── errors/                     # Error Handling Framework
│   ├── __init__.py
│   ├── exceptions.py           # Custom exception classes
│   └── handlers.py             # Error handling decorators
├── db/                         # Database Operations
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy ORM models
│   └── manager.py              # DatabaseManager class
├── topology/                   # Topology Generation
│   ├── __init__.py
│   └── generator.py            # TopologyGenerator class
├── bridges/                    # Bridge Management
│   ├── __init__.py
│   └── manager.py              # BridgeManager class
└── commands/                   # CLI Command Implementations
    ├── __init__.py
    ├── import_csv.py           # CSV import command
    ├── generate_topology.py    # Topology generation command
    ├── bridge_commands.py      # Bridge management commands
    └── data_commands.py        # Data management commands
```

## Core Components

### Configuration Management (`clab_tools/config/`)

#### Purpose
Centralized configuration management with validation and multiple sources.

#### Key Features
- **Pydantic Validation**: Type-safe configuration with automatic validation
- **Hierarchical Settings**: File → Environment → CLI override priority
- **Environment Variables**: Automatic CLAB_* prefix mapping
- **Configuration Files**: YAML-based configuration with inheritance

#### Architecture
```python
class Settings(BaseSettings):
    """Main settings class with nested configurations."""
    database: DatabaseSettings
    logging: LoggingSettings
    topology: TopologySettings
    bridges: BridgeSettings
    debug: bool = False
```

#### Usage Pattern
```python
from clab_tools.config import get_settings

settings = get_settings()
db_url = settings.database.url
log_level = settings.logging.level
```

### Structured Logging (`clab_tools/logging/`)

#### Purpose
Professional logging with structured data and multiple output formats.

#### Key Features
- **Structlog Integration**: Structured logging with context
- **Multiple Formats**: Console (Rich) and JSON output
- **Log Levels**: Configurable verbosity
- **File Rotation**: Automatic log file management
- **Function Tracing**: Automatic function call logging in debug mode

#### Architecture
```python
# Centralized logger configuration
def setup_logging(config: LoggingSettings) -> None:
    """Configure structured logging based on settings."""

def get_logger(name: str) -> BoundLogger:
    """Get a logger instance for a module."""
```

#### Usage Pattern
```python
from clab_tools.log_config import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", node_count=5, duration=1.23)
```

### Error Handling (`clab_tools/errors/`)

#### Purpose
Comprehensive error management with context and recovery strategies.

#### Key Features
- **Custom Exception Classes**: Specific exceptions for different error types
- **Error Context**: Rich error information with operation details
- **Error Decorators**: Reusable error handling patterns
- **Graceful Degradation**: Proper error recovery without crashes

#### Exception Hierarchy
```python
ClabToolsError (Base)
├── ConfigurationError
├── DatabaseError
├── TopologyError
├── BridgeError
├── CSVImportError
└── ValidationError
```

#### Usage Pattern
```python
from clab_tools.errors import DatabaseError, error_handler

@error_handler
def database_operation():
    try:
        # Database operation
        pass
    except Exception as e:
        raise DatabaseError(f"Operation failed: {e}") from e
```

### Database Layer (`clab_tools/db/`)

#### Purpose
Modern ORM-based database operations with connection management.

#### Key Features
- **SQLAlchemy ORM**: Type-safe database operations
- **Connection Pooling**: Efficient connection management
- **Health Checks**: Automatic connection validation
- **Session Management**: Automatic session cleanup
- **Migration Support**: Schema evolution with Alembic

#### Models
```python
class Node(Base):
    """Network node representation."""
    __tablename__ = 'nodes'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(100))
    mgmt_ip: Mapped[str] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(default=func.now())

class Connection(Base):
    """Network connection representation."""
    __tablename__ = 'connections'

    id: Mapped[int] = mapped_column(primary_key=True)
    node1_name: Mapped[str] = mapped_column(ForeignKey('nodes.name'))
    node2_name: Mapped[str] = mapped_column(ForeignKey('nodes.name'))
    type: Mapped[str] = mapped_column(String(50))
    node1_interface: Mapped[str] = mapped_column(String(100))
    node2_interface: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

#### Usage Pattern
```python
from clab_tools.db import DatabaseManager

async with DatabaseManager() as db:
    nodes = await db.get_all_nodes()
    connections = await db.get_all_connections()
```

### Topology Generation (`clab_tools/topology/`)

#### Purpose
Generate containerlab YAML files from database data using templates.

#### Key Features
- **Jinja2 Templates**: Flexible template-based generation
- **YAML Validation**: Automatic output validation
- **Custom Variables**: Template variable injection
- **Multiple Templates**: Support for different topology types

#### Architecture
```python
class TopologyGenerator:
    """Generate containerlab topologies from database data."""

    def generate_topology(
        self,
        nodes: List[Node],
        connections: List[Connection],
        config: TopologyGenerationConfig
    ) -> str:
        """Generate topology YAML from data."""
```

#### Usage Pattern
```python
from clab_tools.topology import TopologyGenerator

generator = TopologyGenerator()
yaml_content = generator.generate_topology(nodes, connections, config)
```

### Bridge Management (`clab_tools/bridges/`)

#### Purpose
Manage Linux bridges for network topology deployment.

#### Key Features
- **Bridge Creation**: Automated Linux bridge setup
- **Dry Run Mode**: Preview operations without execution
- **Verification**: Confirm bridge creation success
- **Cleanup**: Automatic bridge removal

#### Architecture
```python
class BridgeManager:
    """Manage Linux bridges for containerlab topologies."""

    def create_bridges(self, connections: List[Connection], dry_run: bool = False) -> None:
        """Create bridges for network connections."""

    def cleanup_bridges(self, dry_run: bool = False, force: bool = False) -> None:
        """Remove created bridges."""
```

### CLI Commands (`clab_tools/commands/`)

#### Purpose
Implement CLI command logic with proper error handling and logging.

#### Key Features
- **Click Integration**: Modern CLI framework
- **Input Validation**: Comprehensive parameter validation
- **Progress Feedback**: User-friendly operation feedback
- **Error Recovery**: Graceful error handling

#### Command Structure
```python
@click.command()
@click.option('--nodes-csv', required=True, help='Nodes CSV file')
@click.option('--connections-csv', required=True, help='Connections CSV file')
@click.option('--clear-existing', is_flag=True, help='Clear existing data')
@error_handler
def import_csv(nodes_csv: str, connections_csv: str, clear_existing: bool) -> None:
    """Import CSV data into database."""
```

## Data Flow

### CSV Import Flow

```
1. CLI Input Validation
   ↓
2. CSV File Reading (pandas)
   ↓
3. Data Validation (pydantic)
   ↓
4. Database Transaction
   ↓
5. Success/Error Response
```

### Topology Generation Flow

```
1. Database Query
   ↓
2. Template Loading (Jinja2)
   ↓
3. Data Processing
   ↓
4. YAML Generation
   ↓
5. Validation & Output
```

### Bridge Management Flow

```
1. Connection Analysis
   ↓
2. Bridge Planning
   ↓
3. System Commands (with dry-run)
   ↓
4. Verification
   ↓
5. Status Reporting
```

## Design Patterns

### 1. Dependency Injection

```python
class CommandHandler:
    def __init__(self, db_manager: DatabaseManager, logger: BoundLogger):
        self.db_manager = db_manager
        self.logger = logger
```

### 2. Context Managers

```python
class DatabaseManager:
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.session.close()
```

### 3. Factory Pattern

```python
def get_database_manager(settings: Settings) -> DatabaseManager:
    """Factory function for database manager."""
    return DatabaseManager(
        url=settings.database.url,
        echo=settings.database.echo
    )
```

### 4. Decorator Pattern

```python
@error_handler
@log_execution_time
def expensive_operation():
    """Function with automatic error handling and timing."""
    pass
```

## Performance Considerations

### Database Performance
- **Connection Pooling**: Reuse database connections
- **Bulk Operations**: Process multiple records efficiently
- **Query Optimization**: Use appropriate indexes and queries
- **Session Management**: Proper session lifecycle management

### Memory Management
- **Streaming Processing**: Handle large CSV files efficiently
- **Object Lifecycle**: Proper cleanup of resources
- **Generator Usage**: Memory-efficient data processing

### Logging Performance
- **Structured Logging**: Efficient log processing
- **Log Level Filtering**: Avoid expensive operations in disabled log levels
- **Asynchronous Logging**: Non-blocking log operations (when needed)

## Security Architecture

### Input Validation
- **Pydantic Models**: Type-safe input validation
- **Path Validation**: Secure file path handling
- **SQL Injection Prevention**: ORM-based query protection

### Configuration Security
- **Environment Variables**: Secure credential management
- **File Permissions**: Proper configuration file security
- **Secret Management**: No hardcoded secrets

### Error Information
- **Sanitized Errors**: No sensitive data in error messages
- **Context Limiting**: Controlled error context exposure

## Testing Architecture

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── test_config.py           # Configuration tests
├── test_database.py         # Database layer tests
├── test_csv_import.py       # CSV import tests
└── integration/             # Integration tests
    ├── test_workflows.py    # End-to-end workflows
    └── test_cli.py          # CLI integration tests
```

### Test Types
- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component workflows
- **Mock Tests**: External dependency simulation
- **Performance Tests**: Load and stress testing

### Test Fixtures
```python
@pytest.fixture
def db_manager():
    """Provide clean database for testing."""
    # Setup
    yield manager
    # Cleanup

@pytest.fixture
def sample_data():
    """Provide test data."""
    return TestDataFactory.create_sample()
```

## Monitoring and Observability

### Structured Logging
- **Request Tracing**: Track operations across components
- **Performance Metrics**: Execution timing and resource usage
- **Error Context**: Rich error information for debugging

### Health Checks
- **Database Health**: Connection and query health monitoring
- **System Resources**: Memory and disk usage tracking
- **Component Status**: Individual component health reporting

### Metrics Collection
- **Operation Counters**: Track command usage
- **Performance Timers**: Measure operation duration
- **Error Rates**: Monitor failure frequencies

## Future Architecture Considerations

### Planned Enhancements
- **Plugin System**: Extensible command architecture
- **API Server**: REST API for remote operations
- **Web Interface**: Browser-based management UI
- **Distributed Processing**: Multi-node topology management

### Scalability Patterns
- **Microservices**: Service-based architecture
- **Event-Driven**: Asynchronous event processing
- **Caching**: Redis-based caching layer
- **Load Balancing**: Multi-instance deployment

### Technology Evolution
- **Container Deployment**: Docker/Kubernetes deployment
- **Cloud Integration**: Cloud provider integrations
- **Monitoring Integration**: Prometheus/Grafana integration
- **CI/CD Pipelines**: Automated testing and deployment

For more detailed information, see:
- [Developer Guide](developer-guide.md)
- [Configuration Guide](configuration.md)
- [API Reference](api-reference.md)

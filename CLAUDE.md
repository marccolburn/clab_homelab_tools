# Clab-Tools Codebase Guide

This document provides a comprehensive guide to the clab-tools codebase for AI assistants working on this project.

## Project Overview

Clab-tools is a CLI tool for managing containerlab network topologies with multi-lab support, persistent storage, and remote host deployment capabilities.

## Architecture

```
clab-tools/
├── Multi-Lab Database (SQLite)
├── CLI Commands (Grouped)
│   ├── lab (create/switch/delete/list)
│   ├── data (import/show/clear)
│   ├── topology (generate)
│   ├── bridge (create/create-bridge/configure/list/cleanup)
│   └── remote (execute/upload/test)
├── Local & Remote Deployment
└── Configuration Management
```

## Key Components

### 1. Command Structure (Post-Refactor)

Commands are organized into logical groups:

```bash
# Lab management
clab-tools lab create my-lab
clab-tools lab switch production

# Data management
clab-tools data import -n nodes.csv -c connections.csv
clab-tools data show

# Topology generation
clab-tools topology generate -o lab.yml

# Bridge management (flexible)
clab-tools bridge create                    # From topology
clab-tools bridge create-bridge br-mgmt     # Manual creation
clab-tools bridge configure
clab-tools bridge list

# Remote operations
clab-tools remote test-connection
clab-tools remote execute "command"
```

### 2. Database Management (`clab_tools/db/`)

- **DatabaseManager** (`manager.py`): Lab-aware database operations
- **Models** (`models.py`): SQLAlchemy ORM models for Labs, Nodes, Connections
- **Context** (`context.py`): Simplified context helper

Key methods:
```python
# Lab-aware operations
db.get_all_nodes(lab_name=None)  # Uses current lab if not specified
db.insert_node(name, kind, mgmt_ip, lab_name=None)
db.set_lab("production")  # Switch current lab context
```

### 3. Bridge Management (`clab_tools/bridges/`)

**BridgeManager** (`manager.py`) - Enhanced with flexible bridge creation:

```python
# Topology-based bridge creation (existing behavior)
bridge_manager.create_topology_bridges()

# Manual bridge creation with options
bridge_manager.create_bridge(
    "br-mgmt",
    interfaces=["eth0"],
    vlan_filtering=True,
    stp=False,
    vid_range="1-4094"
)

# Specification-based creation (extensibility)
spec = {
    "name": "br-custom",
    "interfaces": ["eth1", "eth2"],
    "vlan_filtering": False
}
bridge_manager.create_bridge_from_spec(spec)
```

### 4. Commands (`clab_tools/commands/`)

Each command module follows patterns:
- Import common utilities: `handle_success`, `handle_error`, `with_lab_context`
- Use lab-aware database context: `get_lab_db(ctx.obj)`
- Support both local and remote operations

**Bridge Commands** (`bridge_commands.py`):
- `create_bridges()` - Topology-based creation
- `create_bridge()` - Manual creation with options
- `configure_vlans()` - VLAN configuration
- `list_bridges()` - Status listing
- `cleanup_bridges()` - Bridge deletion

### 5. Common Utilities (`clab_tools/common/`)

**Utils** (`utils.py`):
```python
def handle_success(message: str) -> None:
    click.echo(f"✓ {message}")

def handle_error(message: str, exit_code: int = 1) -> None:
    click.echo(f"✗ {message}", err=True)
    sys.exit(exit_code)

@with_lab_context
def command_function(ctx):
    # Ensures lab context is available
    pass
```

### 6. Configuration (`clab_tools/config/`)

**Settings** (`settings.py`) - Centralized configuration management:
```python
# Database settings
settings.database.url = "sqlite:///clab_topology.db"

# Topology defaults
settings.topology.name = "clab-topology"
settings.topology.prefix = "clab"

# Remote host settings
settings.remote.host = "192.168.1.100"
settings.remote.user = "clab"
```

## Testing Strategy

### Test Organization
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component workflows
- **CLI Tests**: Command-line interface testing
- **Mock Strategy**: Bridge operations mocked (requires root access)

### Key Test Files
- `test_bridge_manager.py` - Bridge creation and management
- `test_database.py` - Database operations and lab isolation
- `test_csv_import.py` - Data import workflows
- `test_configure_vlans_cli.py` - CLI command testing

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific component
python -m pytest tests/test_bridge_manager.py -v

# Exclude remote tests (require SSH setup)
python -m pytest tests/ -k "not remote" -v
```

## Development Workflow

### Code Style
- Follow existing patterns in each module
- Use type hints where beneficial
- Import common utilities for consistent UI
- Handle both local and remote operations

### Bridge Development
The BridgeManager supports multiple creation patterns:

1. **Topology-based**: Creates bridges from database topology
2. **Manual**: Individual bridge creation with custom options
3. **Specification**: Dictionary-based creation for extensibility

### Remote Operations
Commands support remote execution via:
```python
remote_manager = get_remote_host_manager()
if remote_manager:
    with remote_manager:
        # Execute operations on remote host
        pass
```

## Important Patterns

### Lab Context Management
```python
@with_lab_context
def my_command(ctx):
    db = get_lab_db(ctx.obj)  # Gets lab-aware DatabaseManager
    current_lab = db.get_current_lab()
    # Work with lab-specific data
```

### Error Handling
```python
from clab_tools.common.utils import handle_success, handle_error

try:
    result = perform_operation()
    handle_success("Operation completed successfully")
except Exception as e:
    handle_error(f"Operation failed: {e}")
```

### Bridge Creation Options
```python
# Topology-based (existing behavior)
bridge_manager.create_topology_bridges(dry_run=True)

# Manual with full control
bridge_manager.create_bridge(
    "br-custom",
    vlan_filtering=True,      # Enable VLAN filtering
    stp=False,                # Disable spanning tree
    interfaces=["eth0"],      # Add physical interfaces
    vid_range="100-200",      # Custom VLAN range
    dry_run=True             # Preview mode
)
```

## File Locations

### Core Files
- `clab_tools/main.py` - CLI entry point and command groups
- `clab_tools/db/manager.py` - Lab-aware database operations
- `clab_tools/bridges/manager.py` - Enhanced bridge management
- `clab_tools/commands/bridge_commands.py` - Bridge CLI commands

### Configuration
- `config.yaml` - Default configuration
- `config.local.example.yaml` - Local configuration template
- `supported_kinds.yaml` - Containerlab node types

### Documentation
- `docs/commands.md` - Complete CLI reference
- `docs/user-guide.md` - Usage examples and workflows
- `docs/getting-started.md` - Quick start guide

## Recent Changes (Refactor Phases 1-3)

### Phase 1: Core Simplification
- Made DatabaseManager lab-aware by default
- Removed LabAwareDB wrapper class
- Created common utilities for consistent UI
- Updated all commands to use simplified patterns

### Phase 2: Command Reorganization
- Reorganized flat command structure into logical groups
- Updated all documentation to match new command structure
- Maintained all existing functionality

### Phase 3: Bridge Enhancement
- Enhanced BridgeManager with flexible bridge creation options
- Added manual bridge creation command (`bridge create-bridge`)
- Support for custom VLAN filtering, STP, interfaces, VLAN ranges
- Maintained backward compatibility with topology-based creation

## Future Extensions

The refactored architecture supports:
- Plugin system for additional commands
- Router configuration management (push configs to containerized nodes)
- Enhanced topology validation
- Additional bridge management features

## Common Issues

### Bridge Creation
- Requires root/sudo privileges for bridge operations
- Mock bridge operations in tests (can't run locally)
- Support both local and remote bridge creation

### Lab Isolation
- Each lab maintains separate node/connection data
- Database operations are lab-aware by default
- Switch labs before making changes: `clab-tools lab switch <name>`

### Remote Operations
- SSH key-based authentication recommended
- Test connection before deployment: `clab-tools remote test-connection`
- Commands automatically detect and use remote configuration

This guide should help you understand the codebase structure and development patterns used throughout the project.

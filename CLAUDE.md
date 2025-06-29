# Clab-Tools Codebase Guide

This document provides a comprehensive guide to the clab-tools codebase for AI assistants working on this project.

## CURRENT STATUS (v1.1.1 - Released 2025-06-29)

### ✅ NEW FEATURES IMPLEMENTED (feature/node-exec-config-commands branch - 2025-06-29):
**Node Management Commands with Vendor-Agnostic Drivers**

1. **`node exec` command** - Execute operational commands on network devices
   - ✅ Vendor-agnostic driver architecture with PyEZ for Juniper
   - ✅ Parallel/sequential execution across multiple nodes
   - ✅ Flexible node targeting (by name, kind, list, all)
   - ✅ Multiple output formats (text, table, JSON)
   - ✅ Command timeout and error handling
   - ✅ Progress tracking with rich console output

2. **`node config` command** - Load configurations to network devices
   - ✅ Support for local files (`--file`) and device files (`--device-file`)
   - ✅ Multiple load methods: override, merge, replace
   - ✅ Dry-run capability for configuration validation
   - ✅ Configuration diff display and rollback support
   - ✅ Parallel loading with progress tracking
   - ✅ Comprehensive error handling and reporting

3. **Vendor Driver System** - Extensible architecture for multiple vendors
   - ✅ Abstract base driver interface (`BaseNodeDriver`)
   - ✅ Driver registry with automatic vendor detection
   - ✅ Juniper PyEZ driver implemented (supports vJunos, vMX, vSRX, etc.)
   - ✅ Decorator-based driver registration
   - ✅ Context manager support for resource cleanup
   - 🔄 Future support planned for Nokia SR Linux, Arista cEOS, Cisco IOS-XR

4. **Enhanced Database Schema** - Extended Node model for config management
   - ✅ Vendor, model, OS version tracking fields
   - ✅ Configuration metadata fields (last_config_load, method, status)
   - ✅ Last command execution tracking
   - ✅ SSH authentication fields (username, password, ssh_port)
   - ✅ Credential profile support placeholder

**Key Implementation Files:**
- `clab_tools/node/drivers/base.py` - Abstract driver interface and data classes
- `clab_tools/node/drivers/registry.py` - Driver registration and factory
- `clab_tools/node/drivers/juniper.py` - Juniper PyEZ driver implementation
- `clab_tools/node/command_manager.py` - Command execution orchestration
- `clab_tools/node/config_manager.py` - Configuration loading orchestration
- `clab_tools/commands/node_commands.py` - Enhanced with exec and config commands
- `implementation-plan.md` - Complete technical specification and implementation notes

**Usage Examples:**
```bash
# Execute commands
clab-tools node exec -c "show ospf neighbor" --node router1
clab-tools node exec -c "show version" --kind juniper_vjunosrouter --output-format table
clab-tools node exec -c "show interfaces terse" --all --parallel --max-workers 10

# Load configurations
clab-tools node config -f router.conf --node router1 --dry-run
clab-tools node config -f baseline.conf --kind juniper_vmx --method override
clab-tools node config -d /tmp/device-config.txt --all --method merge --comment "OSPF update"

# Output formats
clab-tools node exec -c "show route" --all --output-format json > routes.json
```

**Implementation Highlights:**
- Clean separation of concerns with manager classes for orchestration
- Driver pattern allows easy addition of new vendors
- Rich progress indicators for long-running operations
- Comprehensive error handling with detailed error messages
- Support for both local and device-based configuration files
- Parallel execution with configurable worker pools
- Multiple output formats for integration with other tools

## Current Development: Node Command & Configuration Management

### Implementation Complete (2025-06-29)

The node exec and config commands have been fully implemented on the `feature/node-exec-config-commands` branch. The implementation includes:

**Completed Components:**
- ✅ Vendor-agnostic driver system with abstract base interface
- ✅ Driver registry for automatic vendor detection and routing
- ✅ Juniper PyEZ driver with comprehensive functionality
- ✅ Command and configuration managers for orchestration
- ✅ Enhanced database schema for metadata tracking
- ✅ CLI commands with rich output formatting
- ✅ Settings extensions for node and vendor configuration
- ✅ All required dependencies added to pyproject.toml

**Ready for Testing:**
The implementation is complete and ready for testing with real containerlab environments. Users can now:
- Execute operational commands on Juniper devices
- Load configurations from local files or device files
- Use dry-run mode to validate configurations
- View configuration diffs before committing
- Execute operations in parallel across multiple nodes

**Next Steps:**
1. Comprehensive unit test suite with mocked PyEZ operations
2. Integration tests with containerlab test environments
3. Additional vendor drivers (Nokia SR Linux, Arista cEOS, Cisco IOS-XR)
4. User documentation updates
5. Configuration template support with Jinja2

### ✅ Latest Fixes (v1.1.1):
1. **Node upload fix** - Fixed "cannot unpack non-iterable Node object" error
2. **Progress bars** - Added file upload progress indicators:
   - Single files show byte-level progress
   - Directories show file count progress (X of Y files)
3. **Topology commands** - Fixed Path handling for both Path objects and strings
4. **Documentation** - Added all missing environment variables to configuration.md

### ✅ Major Features (v1.1.0):
1. **Global `--quiet` flag** for non-interactive scripting
2. **`topology start/stop` commands** with local-first behavior
3. **`node upload` command** for file/directory uploads to nodes
4. **`lab bootstrap/teardown` commands** for complete workflows
5. **Logging configuration** - Added `logging.enabled` option to disable JSON logs

### ✅ All Tests Passing:
**214/214 tests passing with 71% code coverage**

### Key Implementation Details:
- Commands check `ctx.obj.get("quiet", False)` for quiet mode
- Start/stop use `get_containerlab_command()` from utils
- NodeManager in `clab_tools/node/manager.py` handles SSH/SCP
- Bootstrap/teardown use internal CLI calls (not subprocess)
- Bootstrap uses `--clear-existing` for data import
- Logging can be disabled via `CLAB_LOG_ENABLED=false`

## Project Overview

Clab-tools is a CLI tool for managing containerlab network topologies with multi-lab support, persistent storage, and remote host deployment capabilities.

## Architecture

```
clab-tools/
├── Multi-Lab Database (SQLite)
├── CLI Commands (Grouped)
│   ├── lab (create/switch/delete/list/bootstrap/teardown)
│   ├── data (import/show/clear)
│   ├── topology (generate/start/stop)
│   ├── bridge (create/create-bridge/configure/list/cleanup)
│   ├── node (upload)
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
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o lab.yml
clab-tools lab teardown -t lab.yml

# Data management
clab-tools data import -n nodes.csv -c connections.csv
clab-tools data show

# Topology generation and lifecycle
clab-tools topology generate -o lab.yml
clab-tools topology start lab.yml
clab-tools topology stop lab.yml

# Bridge management (flexible)
clab-tools bridge create                    # From topology
clab-tools bridge create-bridge br-mgmt     # Manual creation
clab-tools bridge configure
clab-tools bridge list

# Node management (current)
clab-tools node upload --node router1 --source config.txt --dest /tmp/config.txt
clab-tools node upload --all --source-dir configs/ --dest /etc/

# Node management (in development)
clab-tools node exec -c "show ospf neighbor" --kind juniper_vjunosrouter
clab-tools node config -f router.conf --node router1 --dry-run
clab-tools node config -d /tmp/device-config.txt --all --method merge

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
- **ALWAYS keep all imports at the top of the file** - Never place import statements inside functions or methods
- Always use absolute imports for clab_tools modules

### Testing and Quality Requirements

**CRITICAL**: Before any commit, you MUST:

1. **Run the full test suite**:
   ```bash
   python -m pytest tests/ -v
   ```

2. **Run pre-commit hooks** (handles formatting, linting, etc.):
   ```bash
   pre-commit run --all-files
   ```

3. **Verify all tests pass locally** - CI failures often indicate issues that could be caught locally

**Why this matters**: We've experienced multiple CI failures due to:
- Formatting issues that pre-commit would have caught
- Test failures that could have been detected locally
- Configuration conflicts between development and CI environments

**Testing Configuration Notes**:
- Some tests use `patch` to disable config file discovery for consistent results
- Tests that instantiate `Settings()` may need patching if they expect default values
- Always test configuration changes with both discovery enabled and disabled

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

## Current Development: Node Command & Configuration Management

### 🚧 Implementation Status (feature/node-exec-config-commands)

**Architecture Design Completed:**
- Vendor-agnostic driver system with abstract base interface
- Driver registry for automatic vendor detection and routing
- Command and configuration managers for orchestration
- Enhanced database schema for metadata tracking

**Key Design Decisions:**
1. **PyEZ Integration**: Using Juniper's native PyEZ library for robust JunOS interaction
2. **Dual Configuration Sources**: Support both local files and device filesystem files
3. **Parallel Execution**: Concurrent operations across multiple nodes with progress tracking
4. **Vendor Abstraction**: Driver pattern allows easy addition of new vendors

**Implementation Files Created:**
- `implementation-plan.md` - Complete technical specification and architecture
- Database schema extensions for Node model (vendor, config metadata)
- Driver interface definitions with Juniper PyEZ implementation
- Command and configuration manager classes
- Enhanced CLI commands with rich output formatting

**Next Steps for Implementation:**
1. Create driver infrastructure (`clab_tools/node/drivers/`)
2. Implement Juniper PyEZ driver with connection management
3. Build command and configuration managers
4. Add enhanced CLI commands with dual file source support
5. Extend database schema and migrations
6. Create comprehensive test suite with mocked PyEZ operations

**Testing Strategy:**
- Mock PyEZ Device connections for unit tests
- Integration tests with containerlab environments
- Driver-specific test suites for each vendor
- CLI command testing with various input scenarios

## Future Extensions

The refactored architecture supports:
- Plugin system for additional commands
- Multiple vendor drivers (Nokia SR Linux, Arista cEOS, Cisco IOS-XR)
- Configuration template system with Jinja2
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

## Security Considerations

### Node Credentials
- Store passwords securely (consider using keyring or environment variables)
- Support SSH key authentication where possible
- Warn about plaintext passwords in config files
- Default to SSH keys over passwords

### File Upload
- Validate file paths to prevent directory traversal
- Support secure protocols only (SSH/SFTP)
- Log all upload operations for audit trails

This guide should help you understand the codebase structure and development patterns used throughout the project.

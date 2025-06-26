# API Reference

Complete reference for all CLI commands and options.

## Global Options

These options are available for all commands:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--config` | `-c` | path | `config.yaml` | Path to configuration file |
| `--debug` | | flag | `false` | Enable debug mode with detailed logging |
| `--log-level` | | choice | `INFO` | Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--log-format` | | choice | `console` | Set log format (console, json) |
| `--db-url` | | string | from config | Override database URL |
| `--help` | | flag | | Show help message and exit |

### Global Option Examples

```bash
# Use custom configuration file
python main.py --config production.yaml show-data

# Enable debug mode
python main.py --debug import-csv -n nodes.csv -c connections.csv

# Override log level and format
python main.py --log-level DEBUG --log-format json show-data

# Override database URL
python main.py --db-url "postgresql://user:pass@host/db" show-data

# Combine multiple global options
python main.py --config prod.yaml --debug --log-format json show-data
```

## Commands

### import-csv

Import node and connection data from CSV files into the database.

#### Syntax
```bash
python main.py import-csv [OPTIONS]
```

#### Options

| Option | Short | Type | Required | Description |
|--------|-------|------|----------|-------------|
| `--nodes-csv` | `-n` | path | Yes | CSV file containing node information |
| `--connections-csv` | `-c` | path | Yes | CSV file containing connection information |
| `--clear-existing` | | flag | No | Clear existing data before import |

#### Examples

```bash
# Basic import
python main.py import-csv -n nodes.csv -c connections.csv

# Clear existing data before import
python main.py import-csv -n nodes.csv -c connections.csv --clear-existing

# Import with debug logging
python main.py --debug import-csv -n nodes.csv -c connections.csv

# Import with custom configuration
python main.py --config production.yaml import-csv -n prod_nodes.csv -c prod_connections.csv --clear-existing
```

#### CSV File Requirements

**Nodes CSV Format:**
- **Required columns**: `node_name`, `kind`, `mgmt_ip`
- **File encoding**: UTF-8
- **Header row**: Must be present

**Connections CSV Format:**
- **Required columns**: `node1`, `node2`, `type`, `node1_interface`, `node2_interface`
- **File encoding**: UTF-8
- **Header row**: Must be present
- **Valid types**: `direct`, `bridge`

#### Return Codes
- `0`: Success
- `1`: General error (file not found, invalid format, etc.)
- `2`: Database error
- `3`: Validation error

---

### generate-topology

Generate a containerlab topology YAML file from database data.

#### Syntax
```bash
python main.py generate-topology [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | path | `clab.yml` | Output topology file name |
| `--topology-name` | `-t` | string | `generated_lab` | Topology name |
| `--prefix` | `-p` | string | from config | Topology prefix |
| `--mgmt-network` | `-m` | string | from config | Management network name |
| `--mgmt-subnet` | `-s` | string | from config | Management subnet (CIDR) |
| `--template` | | path | from config | Jinja2 template file |
| `--kinds-config` | | path | from config | Supported kinds configuration file |
| `--validate` | | flag | `false` | Validate generated YAML file |

#### Examples

```bash
# Basic topology generation
python main.py generate-topology

# Custom output file and topology name
python main.py generate-topology -o production_lab.yml -t "production_lab"

# Override management settings
python main.py generate-topology -o lab.yml -m "mgmt_net" -s "192.168.100.0/24"

# Use custom template with validation
python main.py generate-topology --template custom_template.j2 -o lab.yml --validate

# Generate with custom prefix
python main.py generate-topology -o lab.yml -p "prod" -t "production_environment"
```

#### Template Variables

The following variables are available in Jinja2 templates:

| Variable | Type | Description |
|----------|------|-------------|
| `topology_name` | string | Name of the topology |
| `prefix` | string | Containerlab prefix |
| `mgmt_network` | string | Management network name |
| `mgmt_subnet` | string | Management subnet CIDR |
| `nodes` | list | List of node objects |
| `connections` | list | List of connection objects |
| `bridges` | list | List of generated bridge objects |

#### Return Codes
- `0`: Success
- `1`: General error
- `2`: Database error
- `3`: Template error
- `4`: Validation error

---

### create-bridges

Create Linux bridges on the host system for network connections.

#### Syntax
```bash
python main.py create-bridges [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--dry-run` | | flag | `false` | Show what would be done without making changes |
| `--force` | | flag | `false` | Proceed without confirmation prompts |

#### Examples

```bash
# Preview bridge creation (recommended first step)
python main.py create-bridges --dry-run

# Create bridges with confirmation prompts
python main.py create-bridges

# Create bridges without prompts (automation)
sudo python main.py create-bridges --force

# Debug bridge creation
sudo python main.py --debug create-bridges --dry-run
```

#### Requirements
- **Root privileges**: Required for bridge creation (use `sudo`)
- **ip command**: Must be available on the system
- **Database data**: Must have imported connections requiring bridges

#### Bridge Naming Convention
Bridges are named using the pattern: `{bridge_prefix}-{node1}-{interface1}-{node2}-{interface2}`

Example: `clab-br-r1-ge004-r2-ge004`

#### Return Codes
- `0`: Success
- `1`: General error
- `2`: Permission error (need sudo)
- `3`: System command error

---

### cleanup-bridges

Remove Linux bridges created by the tool.

#### Syntax
```bash
python main.py cleanup-bridges [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--dry-run` | | flag | `false` | Show what would be done without making changes |
| `--force` | | flag | `false` | Proceed without confirmation prompts |

#### Examples

```bash
# Preview bridge cleanup
python main.py cleanup-bridges --dry-run

# Remove bridges with confirmation
python main.py cleanup-bridges

# Force cleanup without prompts
sudo python main.py cleanup-bridges --force

# Debug cleanup process
sudo python main.py --debug cleanup-bridges --dry-run
```

#### Requirements
- **Root privileges**: Required for bridge removal (use `sudo`)
- **ip command**: Must be available on the system

#### Return Codes
- `0`: Success
- `1`: General error
- `2`: Permission error (need sudo)
- `3`: System command error

---

### show-data

Display all data stored in the database.

#### Syntax
```bash
python main.py show-data
```

#### Options
This command has no specific options (only global options apply).

#### Examples

```bash
# Show all data
python main.py show-data

# Show data with debug information
python main.py --debug show-data

# Show data from custom database
python main.py --db-url "sqlite:///custom.db" show-data

# Show data in JSON format
python main.py --log-format json show-data
```

#### Output Format
The command displays:
- **Nodes**: All network nodes with their properties
- **Connections**: All network connections with interface details
- **Summary**: Count of nodes and connections

#### Return Codes
- `0`: Success (may show empty database)
- `1`: General error
- `2`: Database error

---

### clear-data

Remove all data from the database.

#### Syntax
```bash
python main.py clear-data [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--force` | | flag | `false` | Skip confirmation prompt |

#### Examples

```bash
# Clear data with confirmation prompt
python main.py clear-data

# Force clear without confirmation (automation)
python main.py clear-data --force

# Clear data from custom database
python main.py --db-url "sqlite:///test.db" clear-data --force
```

#### Warning
This operation is **irreversible**. All nodes, connections, and topology configurations will be permanently deleted.

#### Return Codes
- `0`: Success
- `1`: General error
- `2`: Database error
- `3`: User cancelled operation

---

## Configuration File Reference

### Database Configuration

```yaml
database:
  url: "sqlite:///clab_topology.db"  # Database connection URL
  echo: false                       # Enable SQL query logging
  pool_pre_ping: true              # Enable connection health checks
  pool_size: 5                     # Connection pool size (PostgreSQL/MySQL)
  max_overflow: 10                 # Max additional connections
  pool_timeout: 30                 # Connection timeout seconds
  pool_recycle: 3600              # Recycle connections after seconds
```

### Logging Configuration

```yaml
logging:
  level: "INFO"                    # Log level
  format: "console"                # Output format (console/json)
  file_path: null                  # Log file path (optional)
  max_file_size: 10485760         # Max log file size (bytes)
  backup_count: 5                 # Number of backup log files
  structured: true                # Enable structured logging
```

### Topology Configuration

```yaml
topology:
  default_prefix: "clab"                    # Containerlab prefix
  default_mgmt_network: "clab"             # Management network name
  default_mgmt_subnet: "172.20.20.0/24"   # Management subnet CIDR
  template_path: "topology_template.j2"    # Jinja2 template file
  output_dir: "."                          # Output directory
  validate_output: true                    # Validate generated YAML
  kinds_config_path: "supported_kinds.yaml"
```

### Bridge Configuration

```yaml
bridges:
  bridge_prefix: "clab-br"        # Prefix for bridge names
  cleanup_on_exit: false         # Auto-cleanup bridges on exit
  verify_creation: true          # Verify bridge creation success
  timeout: 30                    # Operation timeout seconds
```

### General Configuration

```yaml
debug: false                     # Global debug mode
```

## Environment Variables Reference

All configuration options can be overridden with environment variables using the `CLAB_` prefix:

| Configuration Path | Environment Variable |
|-------------------|---------------------|
| `database.url` | `CLAB_DATABASE_URL` |
| `database.echo` | `CLAB_DATABASE_ECHO` |
| `logging.level` | `CLAB_LOGGING_LEVEL` |
| `logging.format` | `CLAB_LOGGING_FORMAT` |
| `logging.file_path` | `CLAB_LOGGING_FILE_PATH` |
| `topology.default_prefix` | `CLAB_TOPOLOGY_DEFAULT_PREFIX` |
| `topology.default_mgmt_network` | `CLAB_TOPOLOGY_DEFAULT_MGMT_NETWORK` |
| `topology.default_mgmt_subnet` | `CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET` |
| `bridges.bridge_prefix` | `CLAB_BRIDGES_BRIDGE_PREFIX` |
| `bridges.cleanup_on_exit` | `CLAB_BRIDGES_CLEANUP_ON_EXIT` |
| `debug` | `CLAB_DEBUG` |

### Environment Variable Examples

```bash
# Database settings
export CLAB_DATABASE_URL="postgresql://user:pass@host/db"
export CLAB_DATABASE_ECHO="true"

# Logging settings
export CLAB_LOGGING_LEVEL="DEBUG"
export CLAB_LOGGING_FORMAT="json"
export CLAB_LOGGING_FILE_PATH="/var/log/clab.log"

# Topology settings
export CLAB_TOPOLOGY_DEFAULT_PREFIX="production"
export CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET="10.100.0.0/16"

# Bridge settings
export CLAB_BRIDGES_BRIDGE_PREFIX="prod-br"

# General settings
export CLAB_DEBUG="true"
```

## Error Codes Reference

### Standard Exit Codes

| Code | Name | Description |
|------|------|-------------|
| `0` | SUCCESS | Operation completed successfully |
| `1` | GENERAL_ERROR | General error (file not found, invalid input, etc.) |
| `2` | DATABASE_ERROR | Database operation failed |
| `3` | VALIDATION_ERROR | Input validation failed |
| `4` | TEMPLATE_ERROR | Template processing failed |
| `5` | PERMISSION_ERROR | Insufficient permissions |
| `6` | SYSTEM_ERROR | System command failed |

### Error Handling

All commands provide detailed error messages with context:

```bash
# Example error output
✗ Error: File not found: missing_nodes.csv (Details: {'file_path': 'missing_nodes.csv', 'operation': 'file_read'})
```

## Data Models

### Node Model

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique node identifier |
| `kind` | string | Yes | Device type (from supported_kinds.yaml) |
| `mgmt_ip` | string | Yes | Management IP address |

### Connection Model

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node1` | string | Yes | First node name (must exist in nodes) |
| `node2` | string | Yes | Second node name (must exist in nodes) |
| `type` | string | Yes | Connection type (direct or bridge) |
| `node1_interface` | string | Yes | Interface on first node |
| `node2_interface` | string | Yes | Interface on second node |

### Supported Connection Types

| Type | Description |
|------|-------------|
| `direct` | Direct point-to-point connection between nodes |
| `bridge` | Connection via a dedicated bridge (creates unique bridge per connection) |

## Template Reference

### Available Template Variables

```jinja2
{# Basic topology information #}
{{ topology_name }}      # Topology name
{{ prefix }}            # Containerlab prefix
{{ mgmt_network }}      # Management network name
{{ mgmt_subnet }}       # Management subnet CIDR

{# Data collections #}
{% for node in nodes %}
  {{ node.name }}       # Node name
  {{ node.kind }}       # Node type
  {{ node.mgmt_ip }}    # Management IP
{% endfor %}

{% for connection in connections %}
  {{ connection.node1 }}              # First node
  {{ connection.node2 }}              # Second node
  {{ connection.type }}               # Connection type
  {{ connection.node1_interface }}    # First interface
  {{ connection.node2_interface }}    # Second interface
{% endfor %}

{% for bridge in bridges %}
  {{ bridge.name }}                   # Bridge name
  {{ bridge.connections }}            # Connected interfaces
{% endfor %}
```

### Default Template Structure

```jinja2
name: {{ topology_name }}
prefix: {{ prefix }}
mgmt:
  network: {{ mgmt_network }}
  ipv4-subnet: {{ mgmt_subnet }}

topology:
  nodes:
  {% for node in nodes %}
    {{ node.name }}:
      kind: {{ node.kind }}
      image: {{ node.image }}
      mgmt-ipv4: {{ node.mgmt_ip }}
  {% endfor %}

  links:
  {% for connection in connections %}
    {% if connection.type == 'direct' %}
    - endpoints: ["{{ connection.node1 }}:{{ connection.node1_interface }}", "{{ connection.node2 }}:{{ connection.node2_interface }}"]
    {% endif %}
  {% endfor %}
```

For more information, see:
- [User Guide](user-guide.md)
- [Configuration Guide](configuration.md)
- [Troubleshooting Guide](troubleshooting.md)

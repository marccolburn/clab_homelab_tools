# User Guide

Complete guide for using the Containerlab Homelab Tools for network topology management.

## Overview

The Containerlab Homelab Tools provide a comprehensive CLI interface for managing containerlab network topologies with persistent storage, structured logging, and professional error handling.

## Basic Workflow

### 1. Prepare Your Data

Create CSV files with your network topology data:

**nodes.csv**
```csv
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
sw1,arista_ceos,10.100.100.20
```

**connections.csv**
```csv
node1,node2,type,node1_interface,node2_interface
r1,r2,direct,ge-0/0/1,ge-0/0/1
r1,sw1,bridge,ge-0/0/2,eth1
r2,sw1,bridge,ge-0/0/2,eth2
```

### 2. Import Data

```bash
# Import CSV data into database
python main.py import-csv -n nodes.csv -c connections.csv --clear-existing
```

### 3. Verify Data

```bash
# View imported data
python main.py show-data
```

### 4. Generate Topology

```bash
# Generate containerlab topology file
python main.py generate-topology -o my_lab.yml -t "production_lab" --validate
```

### 5. Create Bridges (Optional)

```bash
# Preview bridge creation
python main.py create-bridges --dry-run

# Create bridges (requires root)
sudo python main.py create-bridges
```

### 6. Deploy with Containerlab

```bash
# Deploy the lab
sudo clab deploy -t my_lab.yml

# When finished, destroy the lab
sudo clab destroy -t my_lab.yml

# Clean up bridges
sudo python main.py cleanup-bridges
```

## CLI Commands Reference

### Global Options

All commands support these global options:

- `--config, -c`: Path to configuration file
- `--debug`: Enable debug mode with detailed logging
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-format`: Set log format (console, json)
- `--db-url`: Override database URL

### Import CSV Data

```bash
python main.py import-csv [OPTIONS]
```

**Options:**
- `-n, --nodes-csv`: CSV file containing node information (required)
- `-c, --connections-csv`: CSV file containing connection information (required)
- `--clear-existing`: Clear existing data before import

**Examples:**
```bash
# Basic import
python main.py import-csv -n nodes.csv -c connections.csv

# Clear existing data before import
python main.py import-csv -n nodes.csv -c connections.csv --clear-existing

# Import with debug logging
python main.py --debug import-csv -n nodes.csv -c connections.csv
```

### Generate Topology

```bash
python main.py generate-topology [OPTIONS]
```

**Options:**
- `-o, --output`: Output topology file name (default: clab.yml)
- `-t, --topology-name`: Topology name (default: generated_lab)
- `-p, --prefix`: Topology prefix (default: from config)
- `-m, --mgmt-network`: Management network name (default: from config)
- `-s, --mgmt-subnet`: Management subnet (default: from config)
- `--template`: Jinja2 template file (default: from config)
- `--kinds-config`: Supported kinds configuration file
- `--validate`: Validate generated YAML file

**Examples:**
```bash
# Basic topology generation
python main.py generate-topology -o lab.yml

# Custom topology with validation
python main.py generate-topology -o production.yml -t "prod_lab" --validate

# Override management settings
python main.py generate-topology -o lab.yml -m "mgmt_net" -s "192.168.100.0/24"
```

### Bridge Management

```bash
python main.py create-bridges [OPTIONS]
python main.py cleanup-bridges [OPTIONS]
```

**Options:**
- `--dry-run`: Show what would be done without making changes
- `--force`: Proceed without confirmation prompts

**Examples:**
```bash
# Preview bridge creation
python main.py create-bridges --dry-run

# Create bridges
sudo python main.py create-bridges

# Force cleanup without prompts
sudo python main.py cleanup-bridges --force
```

### Data Management

```bash
python main.py show-data
python main.py clear-data [OPTIONS]
```

**Options for clear-data:**
- `--force`: Skip confirmation prompt

**Examples:**
```bash
# View all data
python main.py show-data

# Clear all data with confirmation
python main.py clear-data

# Force clear without confirmation
python main.py clear-data --force
```

## Configuration

### Configuration File

Create a `config.yaml` file for persistent settings:

```yaml
# Database settings
database:
  url: "sqlite:///clab_topology.db"
  echo: false                    # Set to true for SQL debugging
  pool_pre_ping: true

# Logging settings
logging:
  level: "INFO"                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "console"              # console or json
  file_path: null                # Optional: "logs/clab.log"
  max_file_size: 10485760        # 10MB
  backup_count: 5

# Topology settings
topology:
  default_prefix: "clab"
  default_mgmt_network: "clab"
  default_mgmt_subnet: "172.20.20.0/24"
  template_path: "topology_template.j2"
  output_dir: "."

# Bridge settings
bridges:
  bridge_prefix: "clab-br"
  cleanup_on_exit: false

# General settings
debug: false
```

### Environment Variables

Override any setting with environment variables:

```bash
export CLAB_DB_URL="postgresql://user:pass@host/db"
export CLAB_LOG_LEVEL="DEBUG"
export CLAB_LOG_FORMAT="json"
export CLAB_DEBUG="true"
export CLAB_TOPOLOGY_DEFAULT_PREFIX="mylab"
```

## CSV File Formats

### Nodes CSV Format

**Required columns:**
- `node_name`: Unique identifier for the node
- `kind`: Device type (must match supported_kinds.yaml)
- `mgmt_ip`: Management IP address

**Example:**
```csv
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
sw1,arista_ceos,10.100.100.20
sw2,arista_ceos,10.100.100.21
```

### Connections CSV Format

**Required columns:**
- `node1`: First node name (must exist in nodes.csv)
- `node2`: Second node name (must exist in nodes.csv)
- `type`: Connection type (direct or bridge)
- `node1_interface`: Interface on first node
- `node2_interface`: Interface on second node

**Example:**
```csv
node1,node2,type,node1_interface,node2_interface
r1,r2,direct,ge-0/0/1,ge-0/0/1
r1,sw1,bridge,ge-0/0/2,eth1
r2,sw1,bridge,ge-0/0/2,eth2
sw1,sw2,direct,eth3,eth1
```

### Connection Types

- **direct**: Creates a direct point-to-point connection between two nodes
- **bridge**: Creates a unique bridge node for each connection and connects both specified nodes to it

## Advanced Usage

### Multiple Configuration Files

```bash
# Use different config for different environments
python main.py --config dev-config.yaml import-csv -n nodes.csv -c connections.csv
python main.py --config prod-config.yaml generate-topology -o prod-lab.yml
```

### Database Operations

```bash
# Use different database
python main.py --db-url "postgresql://user:pass@localhost/clab" show-data

# SQLite with custom path
python main.py --db-url "sqlite:///path/to/custom.db" show-data
```

### Logging Options

```bash
# Console logging with debug level
python main.py --log-format console --log-level DEBUG show-data

# JSON logging for tools
python main.py --log-format json show-data

# Save logs to file (configure in config.yaml)
```

### Template Customization

You can customize the topology template by modifying `topology_template.j2` or creating your own:

```bash
# Use custom template
python main.py generate-topology --template my_template.j2 -o lab.yml
```

## Integration Examples

### Automation Script

```bash
#!/bin/bash
set -e

CONFIG_FILE="production.yaml"
NODES_CSV="nodes.csv"
CONNECTIONS_CSV="connections.csv"
OUTPUT_FILE="lab.yml"

echo "Importing CSV data..."
python main.py --config "$CONFIG_FILE" import-csv -n "$NODES_CSV" -c "$CONNECTIONS_CSV" --clear-existing

echo "Generating topology..."
python main.py --config "$CONFIG_FILE" generate-topology -o "$OUTPUT_FILE" --validate

echo "Creating bridges..."
sudo python main.py --config "$CONFIG_FILE" create-bridges

echo "Deploying lab..."
sudo clab deploy -t "$OUTPUT_FILE"

echo "Lab deployed successfully!"
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Test topology generation
  run: |
    python main.py --log-format json import-csv -n test_nodes.csv -c test_connections.csv
    python main.py --log-format json generate-topology -o test_lab.yml --validate
```

## Best Practices

### 1. Data Management
- Always backup your CSV files before making changes
- Use `--clear-existing` flag when importing new data sets
- Validate CSV files before import

### 2. Configuration
- Use configuration files for consistent settings
- Set appropriate log levels for your environment
- Use environment variables for sensitive settings

### 3. Bridge Management
- Always use `--dry-run` before creating bridges
- Clean up bridges when labs are destroyed
- Monitor bridge creation in production environments

### 4. Error Handling
- Enable debug logging when troubleshooting
- Check log files for detailed error information
- Validate input data before processing

## Common Workflows

### Development Environment
```bash
export CLAB_DEBUG="true"
export CLAB_LOG_LEVEL="DEBUG"
python main.py import-csv -n dev_nodes.csv -c dev_connections.csv --clear-existing
python main.py generate-topology -o dev_lab.yml --validate
```

### Production Environment
```bash
export CLAB_LOG_FORMAT="json"
export CLAB_LOG_LEVEL="INFO"
python main.py --config production.yaml import-csv -n nodes.csv -c connections.csv
python main.py --config production.yaml generate-topology -o production_lab.yml --validate
sudo python main.py --config production.yaml create-bridges
```

### Testing Environment
```bash
export CLAB_DB_URL="sqlite:///:memory:"
python main.py import-csv -n test_nodes.csv -c test_connections.csv
python main.py generate-topology -o test_lab.yml --validate
```

For more advanced usage and troubleshooting, see:
- [Configuration Guide](configuration.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Developer Guide](developer-guide.md)

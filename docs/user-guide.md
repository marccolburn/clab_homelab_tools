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
br-access,bridge,
```

**connections.csv**
```csv
node1,node2,type,node1_interface,node2_interface
r1,r2,direct,ge-0/0/1,ge-0/0/1
r1,br-access,direct,ge-0/0/2,eth21
r2,br-access,direct,ge-0/0/2,eth22
```

> **Note**: This uses the simplified bridge approach where bridges are nodes with `kind=bridge`. Bridge interface names follow the pattern `eth{last_digit_of_node1_interface}{node_id}`. See [Simplified Bridge Guide](simplified-bridge-guide.md) for details.

### 2. Import Data

```bash
# Import CSV data into database
clab-tools import-csv -n nodes.csv -c connections.csv --clear-existing
```

### 3. Verify Data

```bash
# View imported data
clab-tools show-data
```

### 4. Choose Deployment Target

You can deploy containerlab either locally or on a remote host:

#### Local Deployment
```bash
# Create VLAN-capable bridges on the local system
clab-tools create-bridges --dry-run  # Preview first
clab-tools create-bridges            # Create the bridges
```

#### Remote Deployment
```bash
# Configure remote host (one-time setup)
clab-tools --remote-host 192.168.1.100 --remote-user clab-user --enable-remote remote test-connection

# Create bridges on remote host
clab-tools --enable-remote create-bridges

# Or configure in config.yaml:
# remote:
#   enabled: true
#   host: "192.168.1.100"
#   username: "clab-user"
#   password: "your-password"  # or use private_key_path
```

### 5. Generate Topology

#### Local Topology Generation
```bash
# Generate containerlab topology file
clab-tools generate-topology -o my_lab.yml -t "production_lab" --validate
```

#### Remote Topology Generation with Upload
```bash
# Generate and automatically upload to remote host
clab-tools generate-topology --upload --enable-remote -o my_lab.yml -t "production_lab" --validate
```

### 6. Deploy with Containerlab

#### Local Deployment
```bash
# Deploy the lab locally
sudo clab deploy -t my_lab.yml

# When finished, destroy the lab
sudo clab destroy -t my_lab.yml

# Clean up bridges
sudo clab-tools cleanup-bridges
```

#### Remote Deployment
```bash
# Deploy on remote host
clab-tools remote execute "sudo clab deploy -t /tmp/clab-topologies/my_lab.yml"

# Check deployment status
clab-tools remote execute "clab inspect"

# When finished, destroy the lab
clab-tools remote execute "sudo clab destroy -t /tmp/clab-topologies/my_lab.yml"

# Clean up bridges on remote host
clab-tools --enable-remote cleanup-bridges
```

## CLI Commands Reference

### Global Options

All commands support these global options:

- `--config, -c`: Path to configuration file
- `--debug`: Enable debug mode with detailed logging
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-format`: Set log format (console, json)
- `--db-url`: Override database URL

**Remote Host Options (available on all commands):**
- `--remote-host`: Remote containerlab host IP/hostname
- `--remote-user`: Remote host SSH username
- `--remote-password`: Remote host SSH password
- `--remote-port`: Remote host SSH port (default: 22)
- `--remote-key`: Path to SSH private key file
- `--enable-remote`: Enable remote host operations

### Import CSV Data

```bash
clab-tools import-csv [OPTIONS]
```

**Options:**
- `-n, --nodes-csv`: CSV file containing node information (required)
- `-c, --connections-csv`: CSV file containing connection information (required)
- `--clear-existing`: Clear existing data before import

**Examples:**
```bash
# Basic import
clab-tools import-csv -n nodes.csv -c connections.csv

# Clear existing data before import
clab-tools import-csv -n nodes.csv -c connections.csv --clear-existing

# Import with debug logging
clab-tools --debug import-csv -n nodes.csv -c connections.csv
```

### Generate Topology

```bash
clab-tools generate-topology [OPTIONS]
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
- `--upload`: Upload topology file to remote host (requires remote configuration)

**Examples:**
```bash
# Basic topology generation
clab-tools generate-topology -o lab.yml

# Custom topology with validation
clab-tools generate-topology -o production.yml -t "prod_lab" --validate

# Override management settings
clab-tools generate-topology -o lab.yml -m "mgmt_net" -s "192.168.100.0/24"

# Generate and upload to remote host
clab-tools generate-topology --upload --enable-remote -o lab.yml

# Generate with remote host specified via CLI
clab-tools --remote-host 192.168.1.100 --remote-user clab --enable-remote generate-topology --upload -o lab.yml
```

### Bridge Management

```bash
clab-tools create-bridges [OPTIONS]
clab-tools cleanup-bridges [OPTIONS]
clab-tools configure-vlans [OPTIONS]
clab-tools list-bridges
```

**Options:**
- `--dry-run`: Show what would be done without making changes
- `--force`: Proceed without confirmation prompts (create/cleanup only)
- `--bridge BRIDGE_NAME`: Target specific bridge (configure-vlans only)

**Examples:**
```bash
# Preview bridge creation locally
clab-tools create-bridges --dry-run

# Create bridges locally
sudo clab-tools create-bridges

# Create bridges on remote host
clab-tools --enable-remote create-bridges

# Configure VLANs on all bridges (after containerlab deployment)
clab-tools configure-vlans --dry-run
sudo clab-tools configure-vlans

# Configure VLANs on specific bridge
clab-tools configure-vlans --bridge br-core

# List bridge status locally
clab-tools list-bridges

# List bridge status on remote host
clab-tools --enable-remote list-bridges

# Force cleanup without prompts on remote host
clab-tools --enable-remote cleanup-bridges --force
```

> **Important**: The `configure-vlans` command should be run **after** containerlab has deployed your topology and connected interfaces to the bridges. This ensures VLAN traffic can flow properly through all bridge ports by configuring VLAN forwarding on each connected interface.

### Remote Host Management

```bash
clab-tools remote [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
- `test-connection`: Test SSH connection to remote host
- `show-config`: Display current remote host configuration
- `upload-topology LOCAL_FILE REMOTE_PATH`: Upload topology file to remote host
- `execute COMMAND`: Execute command on remote host

**Examples:**
```bash
# Test remote connection
clab-tools remote test-connection --host 192.168.1.100 --username clab-user

# Show current remote configuration
clab-tools remote show-config

# Upload topology file
clab-tools remote upload-topology lab.yml /tmp/clab-topologies/lab.yml

# Execute command on remote host
clab-tools remote execute "clab inspect"

# Deploy containerlab on remote host
clab-tools remote execute "sudo clab deploy -t /tmp/clab-topologies/lab.yml"
```

### Data Management

```bash
clab-tools show-data
clab-tools clear-data [OPTIONS]
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
  default_topology_name: "homelab"
  default_mgmt_network: "clab"
  default_mgmt_subnet: "172.20.20.0/24"
  template_path: "topology_template.j2"
  output_dir: "."

# Bridge settings
bridges:
  bridge_prefix: "clab-br"
  cleanup_on_exit: false

# Remote host settings
remote:
  enabled: false                 # Enable/disable remote operations
  host: "192.168.1.100"         # Remote containerlab host IP/hostname
  port: 22                      # SSH port
  username: "clab-user"         # SSH username
  password: "secure-password"   # SSH password (or use private_key_path)
  private_key_path: "~/.ssh/id_rsa"  # SSH private key (recommended over password)
  topology_remote_dir: "/tmp/clab-topologies"  # Remote directory for topology files
  timeout: 30                   # SSH connection timeout in seconds

# General settings
debug: false
```

### Environment Variables

Override any setting with environment variables:

**General Settings:**
```bash
export CLAB_DB_URL="postgresql://user:pass@host/db"
export CLAB_LOG_LEVEL="DEBUG"
export CLAB_LOG_FORMAT="json"
export CLAB_DEBUG="true"
export CLAB_TOPOLOGY_DEFAULT_PREFIX="mylab"
export CLAB_TOPOLOGY_DEFAULT_TOPOLOGY_NAME="my_lab"
```

**Remote Host Settings:**
```bash
export CLAB_REMOTE_ENABLED="true"
export CLAB_REMOTE_HOST="192.168.1.100"
export CLAB_REMOTE_USERNAME="clab-user"
export CLAB_REMOTE_PASSWORD="secure-password"
export CLAB_REMOTE_PORT="22"
export CLAB_REMOTE_PRIVATE_KEY_PATH="~/.ssh/id_rsa"
export CLAB_REMOTE_TOPOLOGY_REMOTE_DIR="/tmp/clab-topologies"
export CLAB_REMOTE_TIMEOUT="30"
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

- **direct**: Creates a direct point-to-point connection between two nodes (including bridge nodes)

**Bridge Connections**: To connect nodes to bridges, reference the bridge by name in the `node2` column and use the bridge interface naming convention `eth{last_digit}{node_id}`.

**Examples:**
- `r1,r2,direct,ge-0/0/1,ge-0/0/1` - Direct router-to-router connection
- `r1,br-access,direct,ge-0/0/2,eth21` - Router r1 to bridge (interface naming: last digit 2 + node ID 1)

For detailed bridge configuration, see the [Simplified Bridge Guide](simplified-bridge-guide.md).

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

## Remote Host Workflows

### Complete Remote Deployment Workflow

This example shows a complete workflow for deploying containerlab on a remote host:

```bash
#!/bin/bash
set -e

# Step 1: Configure remote host
export CLAB_REMOTE_ENABLED="true"
export CLAB_REMOTE_HOST="192.168.1.100"
export CLAB_REMOTE_USERNAME="clab-user"
export CLAB_REMOTE_PRIVATE_KEY_PATH="~/.ssh/id_rsa"

# Step 2: Test remote connection
echo "Testing remote connection..."
python main.py remote test-connection

# Step 3: Import data locally
echo "Importing CSV data..."
python main.py import-csv -n nodes.csv -c connections.csv --clear-existing

# Step 4: Generate and upload topology
echo "Generating and uploading topology..."
python main.py generate-topology --upload --validate -o my_lab.yml

# Step 5: Create bridges on remote host
echo "Creating bridges on remote host..."
python main.py create-bridges --enable-remote

# Step 6: Deploy on remote host
echo "Deploying lab on remote host..."
python main.py remote execute "sudo clab deploy -t /tmp/clab-topologies/my_lab.yml"

echo "Remote lab deployment complete!"
echo "Check status with: python main.py remote execute 'clab inspect'"
```

### Remote Host Configuration Methods

#### Method 1: Configuration File (Recommended)
```yaml
# config.yaml
remote:
  enabled: true
  host: "192.168.1.100"
  username: "clab-user"
  private_key_path: "~/.ssh/id_rsa"  # Recommended over password
  topology_remote_dir: "/tmp/clab-topologies"
  timeout: 30
```

#### Method 2: Environment Variables
```bash
export CLAB_REMOTE_ENABLED="true"
export CLAB_REMOTE_HOST="192.168.1.100"
export CLAB_REMOTE_USERNAME="clab-user"
export CLAB_REMOTE_PRIVATE_KEY_PATH="~/.ssh/id_rsa"
```

#### Method 3: CLI Arguments
```bash
python main.py --remote-host 192.168.1.100 --remote-user clab-user --remote-key ~/.ssh/id_rsa --enable-remote [command]
```

### Remote Host Management Tasks

#### Initial Setup and Testing
```bash
# Test SSH connectivity
python main.py --remote-host 192.168.1.100 --remote-user clab --enable-remote remote test-connection

# Show current configuration
python main.py remote show-config

# Test with password authentication
python main.py remote test-connection --host 192.168.1.100 --username clab --password
```

#### File Management
```bash
# Upload topology file manually
python main.py remote upload-topology local_lab.yml /tmp/clab-topologies/lab.yml

# Generate and auto-upload
python main.py generate-topology --upload --enable-remote

# Check remote directory contents
python main.py remote execute "ls -la /tmp/clab-topologies/"
```

#### Bridge Management
```bash
# Check bridge status on remote host
python main.py --enable-remote list-bridges

# Create bridges with preview
python main.py --enable-remote create-bridges --dry-run
python main.py --enable-remote create-bridges

# Clean up bridges
python main.py --enable-remote cleanup-bridges
```

#### Containerlab Operations
```bash
# Deploy lab
python main.py remote execute "sudo clab deploy -t /tmp/clab-topologies/lab.yml"

# Check lab status
python main.py remote execute "clab inspect"

# Show lab topology
python main.py remote execute "clab graph -t /tmp/clab-topologies/lab.yml"

# Destroy lab
python main.py remote execute "sudo clab destroy -t /tmp/clab-topologies/lab.yml"
```

### Security Considerations for Remote Hosts

1. **Use SSH Key Authentication** (Recommended)
   ```bash
   # Generate SSH key pair
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/clab_rsa

   # Copy public key to remote host
   ssh-copy-id -i ~/.ssh/clab_rsa.pub clab-user@192.168.1.100

   # Configure in clab-tools
   export CLAB_REMOTE_PRIVATE_KEY_PATH="~/.ssh/clab_rsa"
   ```

2. **Secure Password Handling**
   ```bash
   # Use environment variable (not in config file)
   export CLAB_REMOTE_PASSWORD="secure-password"

   # Or prompt for password interactively
   python main.py remote test-connection --host 192.168.1.100 --username clab
   ```

3. **Network Security**
   - Ensure SSH port (22) is accessible
   - Use VPN or secure networks for remote access
   - Consider SSH port forwarding for additional security

### Remote Host Requirements

Your remote containerlab host should have:

1. **SSH server** running and accessible
2. **Containerlab** installed and working
3. **Bridge utilities** (`bridge-utils` package)
4. **iproute2** package for `ip` commands
5. **Sudo privileges** for the remote user (for bridge and containerlab operations)
6. **Python 3.7+** (if needed for any Python-based tools)

### Troubleshooting Remote Connections

#### Connection Issues
```bash
# Test basic SSH connectivity
ssh clab-user@192.168.1.100

# Test with specific port
ssh -p 2222 clab-user@192.168.1.100

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa

# Debug SSH connection
python main.py --debug remote test-connection
```

#### Permission Issues
```bash
# Test sudo access on remote host
python main.py remote execute "sudo whoami"

# Check if user can manage bridges
python main.py remote execute "sudo ip link show"

# Verify containerlab installation
python main.py remote execute "clab version"
```

#### File Transfer Issues
```bash
# Test SFTP access
sftp clab-user@192.168.1.100

# Check remote directory permissions
python main.py remote execute "ls -la /tmp/"

# Create remote directory manually
python main.py remote execute "mkdir -p /tmp/clab-topologies"
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

### 4. Remote Host Management
- Use SSH key authentication instead of passwords
- Test remote connectivity before running complex operations
- Use `--dry-run` for bridge operations on remote hosts
- Keep remote topology directory organized
- Monitor disk space on remote hosts
- Use timeouts appropriate for your network latency

### 5. Error Handling
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

### Remote Deployment Environment
```bash
export CLAB_REMOTE_ENABLED="true"
export CLAB_REMOTE_HOST="192.168.1.100"
export CLAB_REMOTE_USERNAME="clab-user"
export CLAB_REMOTE_PRIVATE_KEY_PATH="~/.ssh/id_rsa"

python main.py import-csv -n nodes.csv -c connections.csv --clear-existing
python main.py generate-topology --upload --validate -o lab.yml
python main.py create-bridges --enable-remote
python main.py remote execute "sudo clab deploy -t /tmp/clab-topologies/lab.yml"
```

### Testing Environment
```bash
export CLAB_DB_URL="sqlite:///:memory:"
python main.py import-csv -n test_nodes.csv -c test_connections.csv
python main.py generate-topology -o test_lab.yml --validate
```

For more advanced usage and troubleshooting, see:
- [Remote Host Management Guide](remote-host-management.md)
- [Configuration Guide](configuration.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Developer Guide](developer-guide.md)

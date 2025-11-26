# User Guide

Complete guide to using clab-tools for containerlab topology management.

## Overview

clab-tools provides a workflow for managing complex containerlab topologies through:

- **CSV-based data management** - Import/export nodes and connections
- **Multi-lab organization** - Track multiple lab environments
- **Bridge management** - Create and configure network bridges
- **Remote deployment** - Deploy topologies to remote hosts
- **Topology generation** - Generate containerlab YAML from data

## Basic Workflow

### 1. Initialize Project

```bash
# Start new project
clab-tools lab create my-lab
clab-tools lab switch my-lab

# Import topology data
clab-tools data import -n nodes.csv -c connections.csv

# Verify data
clab-tools data show
```

### 2. Configure Bridges

```bash
# Create management bridge
sudo clab-tools bridge create-bridge br-mgmt --interface eth0

# List bridges
clab-tools bridge list

# Configure bridge settings
sudo clab-tools bridge configure
```

### 3. Generate and Deploy Topology

```bash
# Generate containerlab topology
clab-tools topology generate -o lab.yml

# Deploy locally
clab-tools topology start lab.yml

# Or deploy to remote host (with remote configured)
clab-tools --enable-remote topology start lab.yml --remote
```

## Quick Start with Bootstrap

The bootstrap command provides a one-command setup for your entire lab:

```bash
# Complete lab setup from CSV files
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o lab.yml

# Bootstrap without starting (prepare only)
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o lab.yml --no-start

# Bootstrap in quiet mode for automation
clab-tools --quiet lab bootstrap -n nodes.csv -c connections.csv -o lab.yml
```

This single command will:
1. Import your CSV data
2. Generate the topology file
3. Upload to remote host (if configured)
4. Create required bridges
5. Start the containerlab topology
6. Configure VLANs on bridges

To tear down the lab:

```bash
# Complete teardown
clab-tools lab teardown -t lab.yml

# Teardown but keep data
clab-tools lab teardown -t lab.yml --keep-data
```

## Scripting and Automation

### Using Quiet Mode

The `--quiet` flag suppresses all interactive prompts, making commands suitable for scripts:

```bash
# Non-interactive lab creation
clab-tools --quiet lab create production

# Force delete without prompts
clab-tools --quiet lab delete old-lab --force

# Clear data without confirmation
clab-tools --quiet data clear --force

# Bootstrap without any prompts
clab-tools --quiet lab bootstrap -n nodes.csv -c connections.csv -o lab.yml
```

### Example Automation Script

```bash
#!/bin/bash
set -e

# Set quiet mode for all commands
export CLAB_QUIET=true

# Create and setup lab
clab-tools lab create automated-lab
clab-tools lab switch automated-lab
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o topology.yml

# Upload configurations to nodes
clab-tools node upload --all --source init-config.sh --dest /tmp/init.sh
clab-tools node upload --kind srx --source juniper.conf --dest /etc/juniper.conf

# Run commands on remote host
clab-tools remote execute "sudo clab inspect"
```

## Node Management

### Uploading Files to Nodes

Upload files directly to containerlab nodes using their management IPs:

```bash
# Upload to specific node
clab-tools node upload --node router1 --source config.txt --dest /tmp/config.txt

# Upload to all nodes of a kind
clab-tools node upload --kind linux --source startup.sh --dest /opt/startup.sh

# Upload to multiple specific nodes
clab-tools node upload --nodes r1,r2,r3 --source update.sh --dest /tmp/update.sh

# Upload to all nodes in the lab
clab-tools node upload --all --source banner.txt --dest /etc/banner

# Upload directory recursively
clab-tools node upload --node server1 --source-dir ./configs --dest /etc/app/
```

### Executing Commands on Nodes

Execute operational commands on network devices using vendor-specific drivers:

```bash
# Check version on a single node
clab-tools node exec -c "show version" --node router1

# Check OSPF neighbors on all Juniper routers
clab-tools node exec -c "show ospf neighbor" --kind juniper_vjunosrouter

# Get interface status from multiple nodes in parallel
clab-tools node exec -c "show interfaces terse" --nodes router1,router2,router3 --parallel

# Collect routing tables from all nodes in JSON format
clab-tools node exec -c "show route" --all --output-format json > routes.json

# Use table format for structured output
clab-tools node exec -c "show bgp summary" --all --output-format table
```

#### Common Use Cases

**Health Checks:**
```bash
# Check system uptime across all nodes
clab-tools node exec -c "show system uptime" --all --parallel

# Verify interface status
clab-tools node exec -c "show interfaces terse | match up" --kind juniper
```

**Troubleshooting:**
```bash
# Check specific protocol status
clab-tools node exec -c "show ospf neighbor detail" --node router1

# Collect logs with extended timeout
clab-tools node exec -c "show log messages | last 100" --all --timeout 60
```

**Automation:**
```bash
# Export BGP routes for analysis
clab-tools --quiet node exec -c "show route protocol bgp" --all \
  --output-format json > bgp_routes.json

# Monitor interface errors
clab-tools node exec -c "show interfaces extensive | match error" \
  --kind juniper_vmx --output-format table
```

### Loading Configurations to Nodes

Apply configurations to network devices with validation and rollback support:

```bash
# Load configuration from local file
clab-tools node config -f router.conf --node router1

# Validate configuration before applying (dry-run)
clab-tools node config -f changes.conf --node router1 --dry-run

# Load configuration on all vMX routers
clab-tools node config -f vmx-baseline.conf --kind juniper_vmx

# Apply configuration in parallel to all nodes
clab-tools node config -f baseline.conf --all --parallel --comment "Initial baseline"
```

#### Configuration Management Workflows

**Safe Configuration Changes:**
```bash
# 1. Preview the configuration diff
clab-tools node config -f ospf-update.conf --node router1 --diff

# 2. Validate with dry-run
clab-tools node config -f ospf-update.conf --node router1 --dry-run

# 3. Apply the configuration
clab-tools node config -f ospf-update.conf --node router1 --comment "OSPF area update"

# 4. If issues arise, rollback
clab-tools node config --rollback --node router1
```

**Bulk Configuration Updates:**
```bash
# Update ACLs on all edge routers
clab-tools node config -f edge-acl.conf --nodes edge1,edge2,edge3 \
  --method merge --comment "Security ACL update"

# Replace entire configuration (use with caution)
clab-tools node config -f full-config.xml --node router1 --method replace
```

**Device File Loading:**
```bash
# Load configuration stored on device
clab-tools node config -d /tmp/rescue.conf --node router1

# Useful for configurations generated on the device
clab-tools node config -d /var/tmp/generated.conf --all --dry-run
```

### Node Authentication

Configure default node credentials in your config file:

```yaml
# config.local.yaml
node:
  default_user: admin
  default_password: admin123  # Warning: Use SSH keys instead
  default_ssh_port: 22
  private_key_path: ~/.ssh/lab_key
  command_timeout: 30
  config_timeout: 60
  max_parallel_workers: 5
```

Or override per command:

```bash
# Use specific credentials
clab-tools node upload --node switch1 --source config.txt --dest /tmp/config.txt \
  --user netadmin --password secret

# Use specific SSH key
clab-tools node upload --all --source init.sh --dest /tmp/init.sh \
  --private-key ~/.ssh/special_key

# Override for exec command
clab-tools node exec -c "show version" --node router1 \
  --user admin --password newsecret

# Override for config command
clab-tools node config -f secure.conf --node router1 \
  --user admin --private-key ~/.ssh/admin_key
```

### Vendor Support

The node exec and config commands use vendor-specific drivers to communicate with network devices:

**Currently Supported:**
- **Juniper**: All JunOS-based devices (vJunos, vMX, vSRX, vQFX, vEX)
  - Uses PyEZ library for native JunOS communication
  - Supports all configuration formats (set, text, XML, JSON)
  - Full rollback and commit capabilities

**Coming Soon:**
- Nokia SR Linux
- Arista cEOS
- Cisco IOS-XR

The system automatically detects the vendor based on the node's kind and selects the appropriate driver.

## Topology Lifecycle Management

### Starting and Stopping Topologies

The new start/stop commands simplify topology management:

```bash
# Start topology locally (default)
clab-tools topology start lab.yml

# Start on remote host
clab-tools topology start lab.yml --remote

# Stop topology
clab-tools topology stop lab.yml

# Use custom path
clab-tools topology start lab.yml --path /custom/topologies/lab.yml
```

### Local vs Remote Execution

By default, start/stop commands run locally. When remote host is configured:

```bash
# Force local execution even with remote configured
clab-tools --enable-remote topology start lab.yml --local

# Force remote execution
clab-tools topology start lab.yml --remote
```

## Multi-Lab Management

### Lab Operations

```bash
# Create and manage labs
clab-tools lab create datacenter-sim
clab-tools lab create campus-network
clab-tools lab list

# Switch between labs
clab-tools lab switch datacenter-sim
clab-tools data show

# Clone existing lab
clab-tools lab clone datacenter-sim datacenter-v2
```

### Data Isolation

Each lab maintains separate:
- Node and connection data
- Bridge configurations
- Remote host assignments
- Topology generations

## CSV Data Management

### Node Data Format

```csv
name,kind,image,mgmt_ipv4,cpu,memory,labels
spine1,juniper_vjunosrouter,,172.20.1.10,2,2048,role=spine
leaf1,juniper_vjunosrouter,,172.20.1.11,1,1024,role=leaf
```

### Connection Data Format

```csv
node_a,interface_a,node_b,interface_b,bridge
spine1,eth1,leaf1,eth1,br-fabric
spine1,eth2,leaf2,eth1,br-fabric
```

### Import and Export

```bash
# Import data
clab-tools data import nodes.csv connections.csv

# Import data with proper flags
clab-tools data import -n nodes.csv -c connections.csv

# Check imported data
clab-tools data show
```

## Bridge Management

### Creating Bridges

#### Topology-Based Bridge Creation

```bash
# Create all bridges required by topology
sudo clab-tools bridge create

# Preview what bridges would be created
sudo clab-tools bridge create --dry-run
```

#### Manual Bridge Creation

```bash
# Basic management bridge with physical interface
sudo clab-tools bridge create-bridge br-mgmt --interface eth0

# Access bridge without VLAN filtering
sudo clab-tools bridge create-bridge br-access --no-vlan-filtering

# Trunk bridge with multiple interfaces and STP
sudo clab-tools bridge create-bridge br-trunk -i eth1 -i eth2 --stp

# Bridge with custom VLAN range
sudo clab-tools bridge create-bridge br-custom --vid-range 100-200
```

### Bridge Configuration

```bash
# Configure VLANs on all topology bridges
sudo clab-tools bridge configure

# Configure VLANs on specific bridge
sudo clab-tools bridge configure --bridge br-mgmt

# Preview VLAN configuration
sudo clab-tools bridge configure --dry-run
```

## Remote Deployment

### Host Configuration

Configure remote hosts in `config.yaml`:

```yaml
remote_hosts:
  - name: "lab-server-1"
    host: "192.168.1.100"
    user: "clab"
    key_file: "~/.ssh/clab_key"
```

### Remote Operations

```bash
# Test connectivity
clab-tools remote test-connection

# Upload topology to remote
clab-tools remote upload lab.yml

# Execute remote commands
clab-tools remote execute "sudo clab inspect"
```

## Advanced Usage

### Topology Customization

```bash
# Generate with custom template
clab-tools topology generate --template custom-template.j2

# Include specific nodes only
clab-tools topology generate --nodes spine1,spine2

# Output to specific file
clab-tools topology generate --output my-topology.yaml
```

### Bulk Operations

```bash
# Clear all data
clab-tools data clear

# Re-import updated data
clab-tools data clear
clab-tools data import -n nodes-updated.csv -c connections.csv

# Manual bridge creation with custom options
sudo clab-tools bridge create-bridge br-custom --interface eth0
```

### Scripting and Automation

```bash
#!/bin/bash
set -e

# Set quiet mode for non-interactive use
export CLAB_QUIET=true

clab-tools lab create prod-network
clab-tools data import -n prod-nodes.csv -c prod-connections.csv
sudo clab-tools bridge create-bridge br-mgmt --interface eth0
clab-tools topology generate -o prod.yml
clab-tools topology start prod.yml
```

## Configuration Management

### Viewing Current Configuration

clab-tools provides commands to inspect your current configuration and understand how settings are being applied:

```bash
# Show all current settings and their sources
clab-tools config show

# Check specific configuration section
clab-tools config show --section remote

# Export configuration for documentation
clab-tools config show --format yaml > current-config.yaml

# List all CLAB environment variables
clab-tools config env
```

### Configuration Sources

Settings are loaded in priority order:
1. Environment variables (highest priority)
2. Configuration file
3. Default values (lowest priority)

The `config show` command displays the source of each setting:
- `[env]` - From environment variable
- `[file]` - From configuration file
- `[default]` - Default value

### Project Settings

Key configuration options in `config.yaml`:

```yaml
database:
  url: "sqlite:///clab_topology.db"

lab:
  current_lab: "production"

remote:
  enabled: true
  host: "192.168.1.100"
  username: "clab"

node:
  default_username: "admin"
  ssh_port: 22
  command_timeout: 30
```

### Environment Variables

Override any setting using environment variables:

```bash
# Remote host configuration
export CLAB_REMOTE_ENABLED=true
export CLAB_REMOTE_HOST="192.168.1.100"
export CLAB_REMOTE_USERNAME="admin"

# Database configuration
export CLAB_DATABASE_URL="sqlite:///custom.db"

# Lab selection
export CLAB_LAB_CURRENT_LAB="staging"

# Logging configuration
export CLAB_LOG_ENABLED=false
export CLAB_LOG_LEVEL="DEBUG"
export CLAB_LOG_FORMAT="console"

# Node defaults
export CLAB_NODE_DEFAULT_USERNAME="admin"
export CLAB_NODE_SSH_PORT=22
```

### Checking Configuration

```bash
# Verify remote is configured
clab-tools config show --section remote

# Check current lab setting
clab-tools config show --section lab

# Confirm database location
clab-tools config show --section database

# See all environment overrides
clab-tools config env
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Validate CSV format
clab-tools data import --validate nodes.csv

# Check CSV headers
head -1 nodes.csv
```

**Bridge Issues:**
```bash
# Check existing bridges
ip link show type bridge

# Run with sudo
sudo clab-tools bridge create-bridge br-test
```

**Remote Connection Issues:**
```bash
# Test SSH manually
ssh -v user@remote-host

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
```

### Debug Mode

```bash
# Enable debug output
clab-tools --debug <command>

# Log to file
clab-tools --debug <command> 2>&1 | tee debug.log
```

## Best Practices

### Data Organization

- Use consistent naming conventions for nodes
- Group related nodes with labels
- Maintain separate CSV files for different network segments
- Keep backup copies of working configurations

### Lab Management

- Use descriptive lab names
- Switch labs before making changes
- Export data before major modifications
- Document lab purposes and configurations

### Bridge Management

- Plan bridge topology before creation
- Use meaningful bridge names
- Document physical interface assignments
- Test bridge connectivity after creation

### Remote Deployment

- Verify SSH connectivity before deployment
- Use SSH keys instead of passwords
- Test on single host before batch deployment
- Monitor remote host resources

## Next Steps

- See [Commands Reference](commands.md) for complete CLI documentation
- Check [CSV Format Guide](csv-format.md) for data format details
- Review [Configuration Guide](configuration.md) for advanced settings
- Read [Remote Setup Guide](remote-setup.md) for multi-host deployment

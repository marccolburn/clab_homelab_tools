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
./clab-tools.sh lab create my-lab
./clab-tools.sh lab switch my-lab

# Import topology data
clab-tools data import nodes.csv connections.csv

# Verify data
clab-tools data show
```

### 2. Configure Bridges

```bash
# Create management bridge
sudo ./clab-tools.sh bridge create br-mgmt --interfaces eth0

# List bridges
./clab-tools.sh bridge list

# Configure bridge settings
./clab-tools.sh bridge configure br-mgmt --stp off
```

### 3. Generate and Deploy Topology

```bash
# Generate containerlab topology
./clab-tools.sh topology generate

# Deploy locally
containerlab deploy -t clab-topology.yaml

# Or deploy to remote host
./clab-tools.sh remote deploy lab-server-1
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

### Node Authentication

Configure default node credentials in your config file:

```yaml
# config.local.yaml
node:
  default_username: admin
  default_password: admin123  # Warning: Use SSH keys instead
  private_key_path: ~/.ssh/lab_key
  ssh_port: 22
```

Or override per command:

```bash
# Use specific credentials
clab-tools node upload --node switch1 --source config.txt --dest /tmp/config.txt \
  --user netadmin --password secret

# Use specific SSH key
clab-tools node upload --all --source init.sh --dest /tmp/init.sh \
  --private-key ~/.ssh/special_key
```

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
./clab-tools.sh lab create datacenter-sim
./clab-tools.sh lab create campus-network
./clab-tools.sh lab list

# Switch between labs
./clab-tools.sh lab switch datacenter-sim
clab-tools data show

# Clone existing lab
./clab-tools.sh lab clone datacenter-sim datacenter-v2
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
./clab-tools.sh remote test-connection lab-server-1

# Deploy topology
./clab-tools.sh remote deploy lab-server-1

# Check remote status
./clab-tools.sh remote status lab-server-1

# Execute remote commands
./clab-tools.sh remote exec lab-server-1 "containerlab inspect"
```

## Advanced Usage

### Topology Customization

```bash
# Generate with custom template
./clab-tools.sh topology generate --template custom-template.j2

# Include specific nodes only
./clab-tools.sh topology generate --nodes spine1,spine2

# Output to specific file
./clab-tools.sh topology generate --output my-topology.yaml
```

### Bulk Operations

```bash
# Clear all data
clab-tools data clear

# Re-import updated data
./clab-tools.sh data clear
./clab-tools.sh data import -n nodes-updated.csv -c connections.csv

# Manual bridge creation with custom options
sudo ./clab-tools.sh bridge create-bridge br-custom --interface eth0
```

### Scripting and Automation

```bash
# Use in scripts
#!/bin/bash
set -e

./clab-tools.sh lab create prod-network
clab-tools data import prod-nodes.csv prod-connections.csv
sudo ./clab-tools.sh bridge create br-mgmt --interfaces eth0
./clab-tools.sh topology generate
./clab-tools.sh remote deploy prod-server
```

## Configuration Management

### Project Settings

Key configuration options in `config.yaml`:

```yaml
project:
  name: "my-homelab"

defaults:
  node_image: "vrnetlab/vr-vjunosrouter:23.2R1.15"
  mgmt_network: "clab-mgmt"

bridges:
  - name: "br-mgmt"
    interfaces: ["eth0"]
```

### Environment Variables

```bash
# Override project name
export CLAB_PROJECT_NAME="test-lab"

# Enable debug logging
export CLAB_LOG_LEVEL="DEBUG"

# Use custom config file
export CLAB_CONFIG_FILE="./test-config.yaml"
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
sudo ./clab-tools.sh bridge create br-test
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
./clab-tools.sh --debug --verbose command

# Log to file
./clab-tools.sh --debug command 2>&1 | tee debug.log
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

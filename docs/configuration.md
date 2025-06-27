# Configuration Guide

This guide covers all configuration options for clab-tools, including project settings, node configurations, and environment customization.

## Configuration Files

### Primary Configuration (`config.yaml`)

The main configuration file defines project-wide settings:

```yaml
# Project Information
project:
  name: "my-homelab"
  description: "My containerlab homelab setup"
  version: "1.0.0"

# Default Node Settings
defaults:
  node_image: "ceos:latest"
  mgmt_network: "clab-mgmt"

# Bridge Configuration
bridges:
  - name: "br-mgmt"
    type: "linux-bridge"
    interfaces: ["eth0", "eth1"]

# Remote Hosts (optional)
remote_hosts:
  - name: "lab-server-1"
    host: "192.168.1.100"
    user: "admin"
    key_file: "~/.ssh/lab_key"
```

### Local Overrides (`config.local.yaml`)

Create this file to override settings without affecting version control:

```yaml
# Override default images for local development
defaults:
  node_image: "my-local-image:latest"

# Add local-only bridges
bridges:
  - name: "br-dev"
    type: "ovs-bridge"
```

## Configuration Sections

### Project Settings

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `project.name` | Project identifier | `"homelab"` | `"datacenter-sim"` |
| `project.description` | Project description | `""` | `"Network simulation"` |
| `project.version` | Project version | `"1.0.0"` | `"2.1.0"` |

### Node Defaults

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `defaults.node_image` | Default container image | `"ceos:latest"` | `"alpine:latest"` |
| `defaults.mgmt_network` | Management network name | `"clab-mgmt"` | `"mgmt-net"` |
| `defaults.cpu` | Default CPU allocation | `1` | `2` |
| `defaults.memory` | Default memory (MB) | `512` | `1024` |

### Bridge Configuration

```yaml
bridges:
  - name: "br-spine"           # Bridge name
    type: "linux-bridge"       # Bridge type (linux-bridge, ovs-bridge)
    interfaces: ["eth1", "eth2"] # Physical interfaces (optional)
    vlan_aware: true           # VLAN support (optional)
    stp: false                 # Spanning tree (optional)
```

### Remote Host Configuration

```yaml
remote_hosts:
  - name: "lab-server-1"       # Host identifier
    host: "192.168.1.100"      # IP address or hostname
    port: 22                   # SSH port (optional, default: 22)
    user: "admin"              # SSH username
    key_file: "~/.ssh/lab_key" # SSH private key path
    sudo: true                 # Require sudo (optional, default: false)
```

## Environment Variables

Override configuration using environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_PROJECT_NAME` | Override project name | `export CLAB_PROJECT_NAME="test-lab"` |
| `CLAB_DEFAULT_IMAGE` | Override default image | `export CLAB_DEFAULT_IMAGE="alpine:3.18"` |
| `CLAB_MGMT_NETWORK` | Override management network | `export CLAB_MGMT_NETWORK="lab-mgmt"` |
| `CLAB_CONFIG_FILE` | Use alternate config file | `export CLAB_CONFIG_FILE="./prod-config.yaml"` |

## Node-Specific Configuration

When importing from CSV or defining nodes, you can override defaults per node:

```csv
name,kind,image,cpu,memory,mgmt_ipv4
router1,ceos,,2,1024,172.20.1.10
switch1,srl,srlinux:latest,1,512,172.20.1.11
```

## Supported Node Kinds

The following node kinds are supported (from `supported_kinds.yaml`):

- **ceos** - Arista cEOS
- **srl** - Nokia SR Linux
- **crpd** - Juniper cRPD
- **vr-sros** - Nokia SR OS
- **linux** - Generic Linux container
- **alpine** - Alpine Linux
- **ubuntu** - Ubuntu Linux

## Configuration Validation

clab-tools validates configuration on startup:

```bash
# Validate current configuration
./clab-tools.sh config validate

# Show effective configuration (with overrides)
./clab-tools.sh config show

# Test remote host connectivity
./clab-tools.sh remote test-connection lab-server-1
```

## Common Patterns

### Multi-Environment Setup

Use different config files for different environments:

```bash
# Development
cp config.local.example.yaml config.local.yaml

# Production
export CLAB_CONFIG_FILE="./prod-config.yaml"
./clab-tools.sh topology generate
```

### Shared Bridge Configuration

For consistent bridge setup across projects:

```yaml
# shared-bridges.yaml
bridges:
  - name: "br-mgmt"
    type: "linux-bridge"
    interfaces: ["ens3"]
  - name: "br-wan"
    type: "linux-bridge"
    interfaces: ["ens4"]
```

```bash
# Merge with main config
./clab-tools.sh config merge shared-bridges.yaml
```

## Troubleshooting

### Configuration Issues

```bash
# Check configuration syntax
./clab-tools.sh config validate

# Show resolved configuration
./clab-tools.sh config show --verbose

# Reset to defaults
cp config.local.example.yaml config.local.yaml
```

### Remote Host Issues

```bash
# Test SSH connectivity
./clab-tools.sh remote test-connection hostname

# Check remote containerlab status
./clab-tools.sh remote status hostname
```

For more configuration troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

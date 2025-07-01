# Configuration Guide

This guide covers all configuration options for clab-tools, including automatic configuration discovery, persistence settings, and environment customization.

## Configuration File Discovery

clab-tools automatically discovers configuration files using a priority-based system. This eliminates the need to specify `--config` on every command.

### Discovery Order

Configuration files are discovered in the following priority order:

1. **Environment Variable**: `CLAB_CONFIG_FILE`
   - Highest priority, allows complete override
   - `export CLAB_CONFIG_FILE="/path/to/custom-config.yaml"`

2. **Project-Specific**: `./clab_tools_files/config.yaml`
   - Project-specific configuration stored with your project
   - Committed to version control for team sharing
   - Perfect for project-specific settings like lab names, prefixes, etc.

3. **Local Override**: `./config.local.yaml`
   - Local developer overrides (typically not committed)
   - Copy from `config.local.example.yaml` and customize
   - Use for personal preferences, local database paths, etc.

4. **Installation Default**: `config.yaml` (in installation directory)
   - System-wide defaults
   - Updated during tool upgrades

### Using Project-Specific Configuration

Create a `clab_tools_files/` directory in your project:

```bash
mkdir clab_tools_files
cp config.local.example.yaml clab_tools_files/config.yaml
# Edit clab_tools_files/config.yaml for your project
git add clab_tools_files/config.yaml
git commit -m "Add project-specific clab-tools configuration"
```

Team members will automatically use the same settings when they run clab-tools.

## Configuration Files

### Primary Configuration (`config.yaml`)

The main configuration file defines project-wide settings:

```yaml
# Project Information
project:
  name: "my-homelab"
  description: "My containerlab homelab setup"
  version: "1.1.1"

# Default Node Settings
defaults:
  node_image: "vrnetlab/vr-vjunosrouter:23.2R1.15"
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
| `project.version` | Project version | `"1.1.1"` | `"2.1.0"` |

### Database Settings

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `database.url` | Database URL | Installation directory | `"sqlite:///custom_path.db"` |
| `database.echo` | Enable SQL logging | `false` | `true` |
| `database.pool_pre_ping` | Connection health checks | `true` | `false` |

**Database Location:**
- **Default**: Database file (`clab_topology.db`) is created in the tool's installation directory
- **Consistent**: Same database location regardless of your current working directory
- **Portable**: Can be overridden per project using config files
- **Override**: Set `database.url` in config or use environment variable `CLAB_DB_URL`

**Example Database Configurations:**

```yaml
# Use project-specific database
database:
  url: "sqlite:///./project_lab.db"

# Use global database for all projects
database:
  url: "sqlite:////home/user/.clab/global.db"

# Use PostgreSQL for production
database:
  url: "postgresql://user:pass@localhost:5432/clab_db"
```

### Lab Settings

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `lab.current_lab` | Active lab name | `"default"` | `"production"` |
| `lab.auto_create_lab` | Auto-create missing labs | `true` | `false` |
| `lab.use_global_database` | Use global database | `false` | `true` |
| `lab.global_database_path` | Global database directory | `null` | `"/home/user/.clab"` |

**Lab Isolation:**
- Each lab maintains separate nodes, connections, and topologies
- Lab switching persists across command invocations
- Labs are automatically created when first accessed (if `auto_create_lab` is true)

### Node Defaults

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `defaults.node_image` | Default container image | `"vrnetlab/vr-vjunosrouter:23.2R1.15"` | `"alpine:latest"` |
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

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `remote.enabled` | Enable remote operations | `false` | `true` |
| `remote.host` | Remote host IP/hostname | `null` | `"192.168.1.100"` |
| `remote.port` | SSH port | `22` | `2222` |
| `remote.username` | SSH username | `null` | `"labuser"` |
| `remote.password` | SSH password | `null` | `"secret"` |
| `remote.private_key_path` | SSH private key path | `null` | `"~/.ssh/lab_key"` |
| `remote.topology_remote_dir` | Remote topology directory | `"/tmp/clab-topologies"` | `"/home/user/topologies"` |
| `remote.timeout` | Connection timeout (seconds) | `30` | `60` |
| `remote.use_sudo` | Use sudo for commands | `true` | `false` |
| `remote.sudo_password` | Sudo password | `null` | `"sudopass"` |

```yaml
# Example remote configuration
remote:
  enabled: true
  host: "lab-server.company.com"
  username: "labuser"
  private_key_path: "~/.ssh/lab_rsa"
  topology_remote_dir: "/home/labuser/clab-topologies"
  use_sudo: true
```

### Node Configuration

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `node.default_user` | Default SSH username for nodes | `"admin"` | `"netadmin"` |
| `node.default_password` | Default SSH password for nodes | `null` | `"nodepass"` |
| `node.default_ssh_port` | Default SSH port for nodes | `22` | `830` |
| `node.connection_timeout` | SSH connection timeout (seconds) | `30` | `45` |
| `node.command_timeout` | Command execution timeout (seconds) | `30` | `60` |
| `node.config_timeout` | Configuration load timeout (seconds) | `60` | `120` |
| `node.private_key_path` | Default SSH key for nodes | `null` | `"~/.ssh/node_key"` |
| `node.max_parallel_workers` | Max workers for parallel operations | `5` | `10` |
| `node.default_load_method` | Default config load method | `"merge"` | `"override"` |

**Security Warning**: Storing passwords in configuration files is not recommended. Use SSH keys or environment variables instead.

```yaml
# Example node configuration
node:
  default_user: "admin"
  # Use SSH key instead of password
  private_key_path: "~/.ssh/containerlab_key"
  default_ssh_port: 22
  connection_timeout: 30
  command_timeout: 30
  config_timeout: 60
  max_parallel_workers: 5
  default_load_method: "merge"
```

### Vendor Configuration

Configure vendor-specific settings and detection rules:

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `node.vendors.<vendor>.patterns` | Kind patterns for vendor detection | Various | `["juniper_*", "vmx"]` |
| `node.vendors.<vendor>.default_user` | Vendor-specific default user | `null` | `"root"` |
| `node.vendors.<vendor>.default_password` | Vendor-specific default password | `null` | `"Juniper"` |
| `node.vendors.<vendor>.default_ssh_port` | Vendor-specific SSH port | `null` | `830` |

```yaml
# Example vendor configuration
node:
  vendors:
    juniper:
      patterns:
        - "juniper_vjunosrouter"
        - "juniper_vjunosswitch"
        - "juniper_vmx"
        - "juniper_vsrx"
        - "vjunos*"
        - "vmx"
        - "vsrx"
      default_user: "root"
      default_password: "Juniper"

    nokia:
      patterns:
        - "nokia_srlinux"
        - "srl"
        - "sr_linux"
      default_user: "admin"
      default_password: "NokiaSrl1!"

    arista:
      patterns:
        - "arista_ceos"
        - "ceos"
      default_user: "admin"
      default_password: "admin"
```

### Driver-Specific Settings

Some drivers may have specific configuration options:

```yaml
# Example with driver-specific settings
node:
  drivers:
    juniper:
      auto_probe_timeout: 30
      gather_facts: false
      normalize: true

    nokia:
      insecure_connection: true
      timeout: 45
```

## Lab Management and Persistence

clab-tools provides persistent lab switching that survives across command invocations.

### Lab Switching

```bash
# Switch to a different lab (persists across commands)
clab-tools lab switch production

# All subsequent commands use the 'production' lab
clab-tools data show
clab-tools topology generate
```

### Lab Settings Persistence

When you switch labs, the setting is automatically saved to your configuration file:

- **Project config exists**: Saves to `./clab_tools_files/config.yaml`
- **Local config exists**: Saves to `./config.local.yaml`
- **No config exists**: Creates `./config.local.yaml`
- **Environment config**: Saves to the file specified by `CLAB_CONFIG_FILE`

This ensures your lab selection persists across terminal sessions and command invocations.

## Environment Variables

Override any configuration setting using environment variables with the `CLAB_` prefix:

### General Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_CONFIG_FILE` | Override config file discovery | `export CLAB_CONFIG_FILE="./prod-config.yaml"` |
| `CLAB_DEBUG` | Enable debug mode | `export CLAB_DEBUG=true` |

### Database Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_DB_URL` | Database URL | `export CLAB_DB_URL="sqlite:///custom.db"` |
| `CLAB_DB_ECHO` | Enable SQL echo logging | `export CLAB_DB_ECHO=true` |
| `CLAB_DB_POOL_PRE_PING` | Enable connection pool pre-ping | `export CLAB_DB_POOL_PRE_PING=false` |

### Lab Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_LAB_CURRENT_LAB` | Current active lab | `export CLAB_LAB_CURRENT_LAB="test-lab"` |
| `CLAB_LAB_USE_GLOBAL_DATABASE` | Use global database | `export CLAB_LAB_USE_GLOBAL_DATABASE=true` |
| `CLAB_LAB_GLOBAL_DATABASE_PATH` | Global database path | `export CLAB_LAB_GLOBAL_DATABASE_PATH="/home/user/.clab"` |
| `CLAB_LAB_AUTO_CREATE_LAB` | Auto-create missing labs | `export CLAB_LAB_AUTO_CREATE_LAB=false` |

### Logging Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_LOG_ENABLED` | Enable/disable logging | `export CLAB_LOG_ENABLED=false` |
| `CLAB_LOG_LEVEL` | Log level | `export CLAB_LOG_LEVEL=DEBUG` |
| `CLAB_LOG_FORMAT` | Log format (json/console) | `export CLAB_LOG_FORMAT=console` |
| `CLAB_LOG_FILE_PATH` | Log file path | `export CLAB_LOG_FILE_PATH="/var/log/clab-tools.log"` |
| `CLAB_LOG_MAX_FILE_SIZE` | Max log file size in bytes | `export CLAB_LOG_MAX_FILE_SIZE=20971520` |
| `CLAB_LOG_BACKUP_COUNT` | Number of log file backups | `export CLAB_LOG_BACKUP_COUNT=10` |

### Topology Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_TOPOLOGY_DEFAULT_PREFIX` | Default topology prefix | `export CLAB_TOPOLOGY_DEFAULT_PREFIX="mylab"` |
| `CLAB_TOPOLOGY_DEFAULT_TOPOLOGY_NAME` | Default topology name | `export CLAB_TOPOLOGY_DEFAULT_TOPOLOGY_NAME="production"` |
| `CLAB_TOPOLOGY_DEFAULT_MGMT_NETWORK` | Default management network | `export CLAB_TOPOLOGY_DEFAULT_MGMT_NETWORK="mgmt"` |
| `CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET` | Default management subnet | `export CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET="10.0.0.0/24"` |
| `CLAB_TOPOLOGY_TEMPLATE_PATH` | Topology template path | `export CLAB_TOPOLOGY_TEMPLATE_PATH="custom_template.j2"` |
| `CLAB_TOPOLOGY_OUTPUT_DIR` | Output directory | `export CLAB_TOPOLOGY_OUTPUT_DIR="/tmp/topologies"` |

### Bridge Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_BRIDGE_BRIDGE_PREFIX` | Bridge name prefix | `export CLAB_BRIDGE_BRIDGE_PREFIX="lab-br"` |
| `CLAB_BRIDGE_CLEANUP_ON_EXIT` | Cleanup bridges on exit | `export CLAB_BRIDGE_CLEANUP_ON_EXIT=true` |

### Remote Host Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_REMOTE_ENABLED` | Enable remote operations | `export CLAB_REMOTE_ENABLED=true` |
| `CLAB_REMOTE_HOST` | Remote host IP/hostname | `export CLAB_REMOTE_HOST="192.168.1.100"` |
| `CLAB_REMOTE_PORT` | SSH port | `export CLAB_REMOTE_PORT=2222` |
| `CLAB_REMOTE_USERNAME` | SSH username | `export CLAB_REMOTE_USERNAME="labuser"` |
| `CLAB_REMOTE_PASSWORD` | SSH password | `export CLAB_REMOTE_PASSWORD="secret"` |
| `CLAB_REMOTE_PRIVATE_KEY_PATH` | SSH private key path | `export CLAB_REMOTE_PRIVATE_KEY_PATH="~/.ssh/lab_key"` |
| `CLAB_REMOTE_TOPOLOGY_REMOTE_DIR` | Remote topology directory | `export CLAB_REMOTE_TOPOLOGY_REMOTE_DIR="/opt/topologies"` |
| `CLAB_REMOTE_TIMEOUT` | SSH connection timeout | `export CLAB_REMOTE_TIMEOUT=60` |
| `CLAB_REMOTE_USE_SUDO` | Use sudo for commands | `export CLAB_REMOTE_USE_SUDO=false` |
| `CLAB_REMOTE_SUDO_PASSWORD` | Sudo password | `export CLAB_REMOTE_SUDO_PASSWORD="sudopass"` |

### Node Settings
| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_NODE_DEFAULT_USERNAME` | Default node SSH username | `export CLAB_NODE_DEFAULT_USERNAME="admin"` |
| `CLAB_NODE_DEFAULT_PASSWORD` | Default node SSH password | `export CLAB_NODE_DEFAULT_PASSWORD="nodepass"` |
| `CLAB_NODE_SSH_PORT` | Default SSH port for nodes | `export CLAB_NODE_SSH_PORT=830` |
| `CLAB_NODE_CONNECTION_TIMEOUT` | SSH connection timeout | `export CLAB_NODE_CONNECTION_TIMEOUT=45` |
| `CLAB_NODE_PRIVATE_KEY_PATH` | Default SSH private key | `export CLAB_NODE_PRIVATE_KEY_PATH="~/.ssh/node_key"` |

### Environment Variable Naming

Environment variables follow the pattern `CLAB_<SECTION>_<SETTING>`:

- `CLAB_DATABASE_URL` → `database.url`
- `CLAB_LAB_CURRENT_LAB` → `lab.current_lab`
- `CLAB_TOPOLOGY_DEFAULT_PREFIX` → `topology.default_prefix`
- `CLAB_REMOTE_HOST` → `remote.host`

## Node-Specific Configuration

When importing from CSV or defining nodes, you can override defaults per node:

```csv
name,kind,image,cpu,memory,mgmt_ipv4
router1,juniper_vjunosrouter,,2,1024,172.20.1.10
switch1,juniper_vjunosrouter,,1,512,172.20.1.11
```

## Supported Node Kinds

The following node kinds are supported (from `supported_kinds.yaml`):

- **juniper_vjunosrouter** - Juniper vJunos Router (vrnetlab/vr-vjunosrouter:23.2R1.15)

Additional kinds can be added by updating the `supported_kinds.yaml` configuration file.

## Configuration Validation

clab-tools validates configuration on startup:

```bash
# Validate current configuration
./clab-tools.sh --help

# Show effective configuration (with overrides)
./clab-tools.sh remote show-config

# Test remote host connectivity
./clab-tools.sh remote test-connection lab-server-1
```

## Configuration Examples

### Example: Development Configuration

Create `config.local.yaml` for personal development settings:

```yaml
# Personal development overrides
database:
  url: "sqlite:///./dev_lab.db"
  echo: true  # Enable SQL debugging

logging:
  level: "DEBUG"
  format: "console"

topology:
  default_prefix: "mydev"
  default_mgmt_subnet: "172.25.0.0/24"
  output_dir: "./my_outputs"

lab:
  current_lab: "development"
  auto_create_lab: true

debug: true
```

### Example: Project-Specific Configuration

Create `clab_tools_files/config.yaml` for team-shared settings:

```yaml
# Project team configuration
topology:
  default_prefix: "datacenter-sim"
  default_topology_name: "dc_lab"
  default_mgmt_network: "dc-mgmt"
  default_mgmt_subnet: "10.100.0.0/16"

bridges:
  bridge_prefix: "dc-br"
  cleanup_on_exit: false

lab:
  current_lab: "datacenter_topology"
  auto_create_lab: true

remote:
  enabled: true
  host: "lab-server.company.com"
  username: "labuser"
  private_key_path: "~/.ssh/lab_rsa"
```

### Example: Production Configuration

Use environment variables for production deployments:

```bash
# Production environment
export CLAB_CONFIG_FILE="/etc/clab-tools/production.yaml"
export CLAB_DB_URL="postgresql://clab:password@db.company.com:5432/production_lab"
export CLAB_LOG_LEVEL="INFO"
export CLAB_LOG_FORMAT="json"
export CLAB_LOG_FILE_PATH="/var/log/clab-tools.log"

# Run commands
clab-tools lab switch production_spine_leaf
clab-tools topology generate
```

## Common Patterns

### Multi-Environment Setup

Use different config files for different environments:

```bash
# Development (automatic discovery)
cp config.local.example.yaml config.local.yaml
clab-tools lab switch dev

# Staging
export CLAB_CONFIG_FILE="./staging-config.yaml"
clab-tools lab switch staging

# Production
export CLAB_CONFIG_FILE="./prod-config.yaml"
clab-tools lab switch production
```

### Team Configuration Sharing

```bash
# Set up project configuration for team
mkdir clab_tools_files
cp config.local.example.yaml clab_tools_files/config.yaml

# Edit for project-specific settings
vim clab_tools_files/config.yaml

# Commit to share with team
git add clab_tools_files/
git commit -m "Add shared lab configuration"

# Team members automatically inherit settings
git pull
clab-tools lab list  # Uses shared config automatically
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

### Configuration Discovery Issues

```bash
# Check which config file is being used
clab-tools --help  # Shows config file in use

# Override config file for testing
export CLAB_CONFIG_FILE="./test-config.yaml"
clab-tools lab current

# Reset to defaults
rm config.local.yaml  # Remove local overrides
rm -rf clab_tools_files/  # Remove project config
```

### Lab Persistence Issues

```bash
# Check current lab setting
clab-tools lab current

# Verify config file contains lab setting
cat config.local.yaml  # or your active config file
grep -A2 "lab:" config.local.yaml

# Force lab switch with explicit save
clab-tools lab switch test_lab
cat config.local.yaml  # Should show updated lab
```

### Database Location Issues

```bash
# Check effective database path
clab-tools data show  # Will show database location on error

# Override database for testing
export CLAB_DB_URL="sqlite:///./test.db"
clab-tools data show

# Reset to default location
unset CLAB_DB_URL
rm config.local.yaml
```

### Environment Variable Issues

```bash
# Show all CLAB environment variables
env | grep CLAB_

# Test specific override
export CLAB_DEBUG=true
clab-tools lab current

# Clear all CLAB variables
env | grep CLAB_ | cut -d= -f1 | xargs unset
```

### Remote Host Issues

```bash
# Test SSH connectivity
./clab-tools.sh remote test-connection hostname

# Check remote containerlab status
./clab-tools.sh remote test-connection
```

For more configuration troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

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

| Variable | Description | Example |
|----------|-------------|---------|
| `CLAB_CONFIG_FILE` | Override config file discovery | `export CLAB_CONFIG_FILE="./prod-config.yaml"` |
| `CLAB_DEBUG` | Enable debug mode | `export CLAB_DEBUG=true` |
| `CLAB_DB_URL` | Override database URL | `export CLAB_DB_URL="sqlite:///custom.db"` |
| `CLAB_LAB_CURRENT_LAB` | Override current lab | `export CLAB_LAB_CURRENT_LAB="test-lab"` |
| `CLAB_TOPOLOGY_DEFAULT_PREFIX` | Override topology prefix | `export CLAB_TOPOLOGY_DEFAULT_PREFIX="mylab"` |
| `CLAB_LOG_LEVEL` | Override log level | `export CLAB_LOG_LEVEL=DEBUG` |

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

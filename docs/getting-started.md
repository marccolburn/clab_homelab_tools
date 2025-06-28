# Getting Started

Quick setup and first steps with clab-tools.

## Installation

### Requirements
- Python 3.9+
- SSH access to remote hosts (if using remote features)
- Root access for bridge creation (local or remote)

### Setup

```bash
# Clone repository
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools

# Install system-wide CLI
./install-cli.sh

# Verify installation
clab-tools --help
```

The install script creates:
- Python virtual environment in the project directory (`.venv/`)
- CLI symlink at `/usr/local/bin/clab-tools` pointing to the project
- Database file in the installation directory (`clab_topology.db`)

## Configuration Discovery

clab-tools automatically discovers configuration files in this order:

1. **Environment Variable**: `CLAB_CONFIG_FILE=/path/to/config.yaml`
2. **Project-Specific**: `./clab_tools_files/config.yaml` (for team sharing)
3. **Local Override**: `./config.local.yaml` (for personal settings)
4. **Installation Default**: Uses built-in defaults

This means you don't need to specify `--config` on every command!

### Quick Configuration Setup

```bash
# Option 1: Create personal local overrides
cp config.local.example.yaml config.local.yaml
# Edit config.local.yaml for your preferences

# Option 2: Create project-specific configuration (recommended for teams)
mkdir clab_tools_files
cp config.local.example.yaml clab_tools_files/config.yaml
# Edit clab_tools_files/config.yaml for project settings
# Commit this file to share settings with your team

# Option 3: Use environment variable for one-off configs
export CLAB_CONFIG_FILE="./special-config.yaml"
```

## First Lab

### 1. Create Lab Environment

```bash
# Create your first lab
clab-tools lab create tutorial -d "My first lab"

# The lab switch is automatically saved and persists!
# Verify lab was created and is active
clab-tools lab list
clab-tools lab current

# Note: Lab switching now persists across command invocations
# You don't need to specify the lab on each command
```

### 2. Prepare CSV Data

Create two CSV files defining your network:

**nodes.csv**
```csv
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
sw1,arista_ceos,10.100.100.20
br-mgmt,bridge,
```

**connections.csv**
```csv
node1,node2,type,node1_interface,node2_interface
r1,r2,direct,ge-0/0/1,ge-0/0/1
r1,br-mgmt,direct,ge-0/0/0,eth1
r2,br-mgmt,direct,ge-0/0/0,eth2
sw1,br-mgmt,direct,eth1,eth3
```

### 3. Import and Verify

```bash
# Import CSV data
clab-tools data import -n nodes.csv -c connections.csv

# View imported data
clab-tools data show
```

### 4. Deploy Locally

```bash
# Generate topology file
clab-tools topology generate -o tutorial.yml -t "tutorial-lab"

# Create required bridges (requires sudo)
sudo clab-tools bridge create

# Deploy with containerlab
sudo clab deploy -t tutorial.yml
```

### 5. Cleanup

```bash
# Destroy containerlab topology
sudo clab destroy -t tutorial.yml

# Remove bridges
sudo clab-tools bridge cleanup

# Remove lab data
clab-tools lab delete tutorial
```

## Next Steps

- [User Guide](user-guide.md) - Complete usage examples
- [Remote Host Setup](remote-setup.md) - Deploy on remote hosts
- [Configuration](configuration.md) - Customize settings

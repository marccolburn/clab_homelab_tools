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

# Create virtual environment and install package
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# Install system-wide CLI
./install-cli.sh

# Verify installation
clab-tools --help
```

The install script:
- Verifies the virtual environment exists and package is installed
- Creates a CLI symlink at `/usr/local/bin/clab-tools` pointing to the project
- Allows running `clab-tools` from anywhere on the system

**Note**: The package must be installed in editable mode (`pip install -e .`) before running `install-cli.sh`. This ensures Python can properly resolve all package imports.

### Essential Configuration (Important!)

Before proceeding with any examples, review and customize the configuration for your environment:

```bash
# Create a local configuration from the example
cp config.local.example.yaml config.local.yaml

# Edit to match your environment
# Key settings to review:
# - bridges: Update interface names to match your system
# - remote: Configure if using remote deployment
# - node: Set default credentials for your devices
# - defaults: Adjust container images and network settings
vim config.local.yaml
```

**Note**: The default `config.yaml` contains example settings that likely won't match your environment. Creating a `config.local.yaml` ensures your settings override the defaults without modifying the original file.

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

### Quick Start with Bootstrap

**Prerequisites**: Ensure you've created and customized your `config.local.yaml` file (see Essential Configuration above).

The fastest way to get started is using the bootstrap command:

```bash
# Complete lab setup in one command
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o tutorial.yml

# This single command will:
# 1. Create and switch to a new lab (if needed)
# 2. Import your CSV data
# 3. Generate the topology file
# 4. Create required bridges
# 5. Start the containerlab topology
# 6. Configure VLANs on bridge interfaces
```

**Note**: The bootstrap command uses settings from your configuration file, including:
- Bridge names and interfaces
- Default container images
- Management network settings
- Remote host settings (if configured)

### Manual Setup (Step-by-Step)

For more control, you can set up your lab manually:

#### 1. Create Lab Environment

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
sw1,juniper_vjunosrouter,10.100.100.20
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

# Start the topology (simplified command)
clab-tools topology start tutorial.yml
# Or deploy with containerlab directly: sudo clab deploy -t tutorial.yml

# Configure VLAN forwarding on bridge interfaces (important!)
sudo clab-tools bridge configure
```

**Note**: The `bridge configure` command sets up VLAN forwarding on the bridge interfaces, which is essential for proper communication between nodes. Without this step, VLANs won't be forwarded correctly between your containerlab nodes.

### 5. Interact with Running Nodes

After your topology is running, you can interact with nodes in multiple ways:

#### Execute Commands

```bash
# Check version on a specific node
clab-tools node exec -c "show version" --node r1

# Check interfaces on all routers
clab-tools node exec -c "show interfaces terse" --kind juniper_vjunosrouter

# Get routing table from all nodes in parallel
clab-tools node exec -c "show route" --all --parallel --output-format table
```

#### Load Configurations

```bash
# Load config to a specific node
clab-tools node config -f router-config.conf --node r1

# First validate with dry-run
clab-tools node config -f baseline.conf --node r1 --dry-run

# Apply baseline to all routers
clab-tools node config -f baseline.conf --kind juniper_vjunosrouter --comment "Initial setup"
```

#### Upload Files

```bash
# Upload initial config to a specific node
clab-tools node upload --node r1 --source router-config.txt --dest /tmp/config.txt

# Upload startup script to all nodes
clab-tools node upload --all --source init.sh --dest /tmp/init.sh

# Upload configs to all routers
clab-tools node upload --kind juniper_vjunosrouter --source juniper.conf --dest /etc/juniper.conf
```

### 6. Cleanup

```bash
# Teardown everything with one command
clab-tools lab teardown -t tutorial.yml

# Or cleanup manually:
# Stop the topology
clab-tools topology stop tutorial.yml

# Remove bridges
sudo clab-tools bridge cleanup

# Remove lab data
clab-tools lab delete tutorial
```

## Scripting and Automation

For automated deployments, use the `--quiet` flag:

```bash
# Non-interactive bootstrap
clab-tools --quiet lab bootstrap -n nodes.csv -c connections.csv -o lab.yml

# Non-interactive teardown
clab-tools --quiet lab teardown -t lab.yml

# Script example
#!/bin/bash
set -e

# Set quiet mode for all commands
export CLAB_QUIET=true

clab-tools lab create automated-lab
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o topology.yml
clab-tools node upload --all --source startup.sh --dest /tmp/startup.sh
```

## Next Steps

- [User Guide](user-guide.md) - Complete usage examples
- [Remote Host Setup](remote-setup.md) - Deploy on remote hosts
- [Configuration](configuration.md) - Customize settings

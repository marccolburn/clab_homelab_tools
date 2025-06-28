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
- Database file in the project directory (`clab_topology.db`)

## First Lab

### 1. Create Lab Environment

```bash
# Create your first lab
clab-tools lab create tutorial -d "My first lab"

# Verify lab was created
clab-tools lab list
clab-tools lab current
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

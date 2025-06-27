# Command Reference

Complete CLI command documentation for clab-tools.

## Global Options

Available with all commands:

```bash
--db-url TEXT           # Database URL override
-c, --config TEXT       # Configuration file path
-l, --lab TEXT          # Lab name override
--debug                 # Enable debug mode
--log-level TEXT        # Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
--log-format TEXT       # Set log format (json, console)
--remote-host TEXT      # Remote containerlab host IP/hostname
--remote-user TEXT      # Remote host username
--remote-password TEXT  # Remote host password
--remote-port INTEGER   # Remote host SSH port
--remote-key TEXT       # Path to SSH private key file
--enable-remote         # Enable remote host operations
```

## Lab Management

### `clab-tools lab`

Manage lab environments.

#### `lab create <name>`

```bash
clab-tools lab create my-lab -d "My Lab Description"
```

**Options:**
- `-d, --description TEXT` - Lab description

#### `lab list`

```bash
clab-tools lab list
```

Shows all labs with creation date and description.

#### `lab current`

```bash
clab-tools lab current
```

Shows current active lab information.

#### `lab switch <name>`

```bash
clab-tools lab switch production-lab
```

Switches to specified lab (sets as current).

#### `lab delete <name>`

```bash
clab-tools lab delete old-lab
```

Deletes lab and all its data permanently.

## Data Management

### `import-csv`

Import node and connection data from CSV files.

```bash
clab-tools import-csv -n nodes.csv -c connections.csv [OPTIONS]
```

**Options:**
- `-n, --nodes-file PATH` - Nodes CSV file (required)
- `-c, --connections-file PATH` - Connections CSV file (required)
- `--clear-existing` - Clear existing data before import

**Examples:**
```bash
# Basic import
clab-tools import-csv -n nodes.csv -c connections.csv

# Replace existing data
clab-tools import-csv -n nodes.csv -c connections.csv --clear-existing

# Import to specific lab
clab-tools --lab production import-csv -n prod-nodes.csv -c prod-connections.csv
```

### `show-data`

Display current lab data.

```bash
clab-tools show-data
```

Shows nodes, connections, and statistics for current lab.

### `clear-data`

Clear all data from current lab.

```bash
clab-tools clear-data --force
```

**Options:**
- `--force` - Skip confirmation prompt

## Topology Generation

### `generate-topology`

Generate containerlab topology file from database.

```bash
clab-tools generate-topology -o lab.yml [OPTIONS]
```

**Options:**
- `-o, --output PATH` - Output YAML file (required)
- `-t, --topology-name TEXT` - Topology name (default: from config)
- `-p, --prefix TEXT` - Node name prefix (default: from config)
- `--validate` - Validate against supported kinds
- `--upload` - Upload to remote host (requires --enable-remote)

**Examples:**
```bash
# Basic generation
clab-tools generate-topology -o my-lab.yml

# Custom name and prefix
clab-tools generate-topology -o lab.yml -t "production" -p "prod"

# Validate containerlab kinds
clab-tools generate-topology -o lab.yml --validate

# Generate and upload to remote
clab-tools generate-topology --upload --enable-remote -o lab.yml
```

## Bridge Management

### `create-bridges`

Create Linux bridges based on connection data.

```bash
sudo clab-tools create-bridges [OPTIONS]
```

**Options:**
- `--dry-run` - Show what would be done without changes
- `--force` - Skip confirmation prompts

**Examples:**
```bash
# Preview bridge creation
sudo clab-tools create-bridges --dry-run

# Create bridges locally
sudo clab-tools create-bridges

# Create bridges on remote host
clab-tools --enable-remote create-bridges --force
```

### `list-bridges`

List bridge status and requirements.

```bash
clab-tools list-bridges
```

Shows required bridges from topology and their current status.

### `configure-vlans`

Configure VLAN forwarding on bridge interfaces.

```bash
sudo clab-tools configure-vlans [OPTIONS]
```

**Options:**
- `--bridge TEXT` - Target specific bridge (default: all bridges)
- `--dry-run` - Show what would be done without changes

**Examples:**
```bash
# Configure VLANs on all bridges
sudo clab-tools configure-vlans

# Configure specific bridge
sudo clab-tools configure-vlans --bridge br-access

# Preview VLAN configuration
sudo clab-tools configure-vlans --dry-run
```

### `delete-bridges`

Delete Linux bridges from the system.

```bash
sudo clab-tools delete-bridges [OPTIONS]
```

**Options:**
- `--dry-run` - Show what would be done without changes
- `--force` - Skip confirmation prompts

**Examples:**
```bash
# Preview bridge deletion
sudo clab-tools delete-bridges --dry-run

# Delete bridges with confirmation
sudo clab-tools delete-bridges

# Force delete without prompts
sudo clab-tools delete-bridges --force
```

## Remote Operations

### `clab-tools remote`

Manage remote containerlab host operations.

#### `remote test-connection`

Test SSH connection to remote host.

```bash
clab-tools --enable-remote remote test-connection
```

#### `remote show-config`

Display current remote host configuration.

```bash
clab-tools remote show-config
```

#### `remote execute <command>`

Execute command on remote host.

```bash
clab-tools --enable-remote remote execute "clab inspect"
```

#### `remote upload-topology <file>`

Upload topology file to remote host.

```bash
clab-tools --enable-remote remote upload-topology lab.yml
```

**Examples:**
```bash
# Test connection with CLI flags
clab-tools --remote-host 192.168.1.100 --remote-user clab --enable-remote remote test-connection

# Execute containerlab commands
clab-tools --enable-remote remote execute "sudo clab deploy -t /tmp/clab-topologies/lab.yml"
clab-tools --enable-remote remote execute "clab inspect"
clab-tools --enable-remote remote execute "sudo clab destroy -t /tmp/clab-topologies/lab.yml"

# Upload topology file
clab-tools --enable-remote remote upload-topology my-lab.yml
```

## Configuration Override Examples

### Lab-Specific Operations

```bash
# Work with specific lab without switching
clab-tools --lab production show-data
clab-tools --lab staging import-csv -n staging.csv -c connections.csv

# Multiple overrides
clab-tools --config custom.yaml --lab special-env --debug generate-topology -o lab.yml
```

### Remote Host Operations

```bash
# Using CLI flags for remote operations
clab-tools --remote-host 10.1.1.100 --remote-user admin --enable-remote create-bridges

# Override remote credentials
clab-tools --remote-host 192.168.1.50 --remote-user clab --remote-password secret --enable-remote remote test-connection
```

### Database Override

```bash
# Use different database
clab-tools --db-url sqlite:///backup.db show-data

# Temporary database for testing
clab-tools --db-url sqlite:///test.db import-csv -n test-nodes.csv -c test-connections.csv
```

### Debug Mode

```bash
# Enable debug logging
clab-tools --debug --log-level DEBUG generate-topology -o lab.yml

# JSON logging format
clab-tools --log-format json --log-level INFO create-bridges
```

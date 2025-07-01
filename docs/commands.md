# Command Reference

Complete CLI command documentation for clab-tools.

## Global Options

Available with all commands:

```bash
--db-url TEXT           # Database URL override
-c, --config TEXT       # Configuration file path
-l, --lab TEXT          # Lab name override
--debug                 # Enable debug mode
-q, --quiet             # Suppress interactive prompts for scripting
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

**Options:**
- `-f, --force` - Skip confirmation prompts

#### `lab bootstrap`

Bootstrap a complete lab environment from CSV files to running topology.

```bash
clab-tools lab bootstrap --nodes nodes.csv --connections connections.csv --output topology.yml [OPTIONS]
```

**Options:**
- `-n, --nodes PATH` - Nodes CSV file (required)
- `-c, --connections PATH` - Connections CSV file (required)
- `-o, --output TEXT` - Output topology file name (required)
- `--no-start` - Skip starting the topology
- `--skip-vlans` - Skip VLAN configuration
- `--dry-run` - Show what would be done without executing

**Workflow Steps:**
1. Import CSV data (clears existing data)
2. Generate topology file with validation
3. Upload topology to remote host (if configured)
4. Create bridges
5. Start containerlab topology
6. Configure VLANs on bridge interfaces

**Examples:**
```bash
# Basic bootstrap
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o lab.yml

# Bootstrap without starting topology
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o lab.yml --no-start

# Preview bootstrap steps
clab-tools lab bootstrap -n nodes.csv -c connections.csv -o lab.yml --dry-run

# Bootstrap with quiet mode for scripting
clab-tools --quiet lab bootstrap -n nodes.csv -c connections.csv -o lab.yml
```

#### `lab teardown`

Teardown a complete lab environment.

```bash
clab-tools lab teardown --topology topology.yml [OPTIONS]
```

**Options:**
- `-t, --topology TEXT` - Topology file name (required)
- `--keep-data` - Keep database entries (don't clear data)
- `--dry-run` - Show what would be done without executing

**Workflow Steps:**
1. Stop containerlab topology
2. Remove bridges
3. Clear database entries (optional)

**Examples:**
```bash
# Basic teardown
clab-tools lab teardown -t lab.yml

# Teardown but keep database entries
clab-tools lab teardown -t lab.yml --keep-data

# Preview teardown steps
clab-tools lab teardown -t lab.yml --dry-run

# Teardown with quiet mode
clab-tools --quiet lab teardown -t lab.yml
```

## Data Management

### `clab-tools data`

Manage lab data including importing, viewing, and clearing.

#### `data import`

Import node and connection data from CSV files.

```bash
clab-tools data import -n nodes.csv -c connections.csv [OPTIONS]
```

**Options:**
- `-n, --nodes-file PATH` - Nodes CSV file (required)
- `-c, --connections-file PATH` - Connections CSV file (required)
- `--clear-existing` - Clear existing data before import

**Examples:**
```bash
# Basic import
clab-tools data import -n nodes.csv -c connections.csv

# Replace existing data
clab-tools data import -n nodes.csv -c connections.csv --clear-existing

# Import to specific lab
clab-tools --lab production data import -n prod-nodes.csv -c prod-connections.csv
```

#### `data show`

Display current lab data.

```bash
clab-tools data show
```

Shows nodes, connections, and statistics for current lab.

#### `data clear`

Clear all data from current lab.

```bash
clab-tools data clear --force
```

**Options:**
- `--force` - Skip confirmation prompt

## Topology Generation

### `clab-tools topology`

Generate and validate containerlab topology files.

#### `topology generate`

Generate containerlab topology file from database.

```bash
clab-tools topology generate -o lab.yml [OPTIONS]
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
clab-tools topology generate -o my-lab.yml

# Custom name and prefix
clab-tools topology generate -o lab.yml -t "production" -p "prod"

# Validate containerlab kinds
clab-tools topology generate -o lab.yml --validate

# Generate and upload to remote
clab-tools topology generate --upload --enable-remote -o lab.yml
```

#### `topology start <file>`

Start a containerlab topology.

```bash
clab-tools topology start topology.yml [OPTIONS]
```

**Options:**
- `-p, --path TEXT` - Custom path for topology file (overrides remote dir)
- `--remote` - Force remote execution
- `--local` - Force local execution (when remote is configured)

**Behavior:**
- Default: Runs locally
- If remote host is configured, uses `remote.topology_remote_dir` unless `--path` is specified
- Use `--remote` to force remote execution
- Use `--local` to force local execution when remote is configured

**Examples:**
```bash
# Start topology locally (default)
clab-tools topology start lab.yml

# Start topology on remote host
clab-tools topology start lab.yml --remote

# Start topology with custom path
clab-tools topology start lab.yml --path /custom/path/lab.yml

# Force local execution when remote is configured
clab-tools --enable-remote topology start lab.yml --local

# Start with quiet mode
clab-tools --quiet topology start lab.yml
```

#### `topology stop <file>`

Stop a containerlab topology.

```bash
clab-tools topology stop topology.yml [OPTIONS]
```

**Options:**
- `-p, --path TEXT` - Custom path for topology file (overrides remote dir)
- `--remote` - Force remote execution
- `--local` - Force local execution (when remote is configured)

**Behavior:**
- Default: Runs locally
- If remote host is configured, uses `remote.topology_remote_dir` unless `--path` is specified
- Use `--remote` to force remote execution
- Use `--local` to force local execution when remote is configured

**Examples:**
```bash
# Stop topology locally (default)
clab-tools topology stop lab.yml

# Stop topology on remote host
clab-tools topology stop lab.yml --remote

# Stop topology with custom path
clab-tools topology stop lab.yml --path /custom/path/lab.yml

# Force local execution when remote is configured
clab-tools --enable-remote topology stop lab.yml --local

# Stop with quiet mode
clab-tools --quiet topology stop lab.yml
```

## Bridge Management

### `clab-tools bridge`

Manage Linux bridges for network connectivity.

#### `bridge create`

Create Linux bridges based on connection data from topology.

```bash
sudo clab-tools bridge create [OPTIONS]
```

**Options:**
- `--dry-run` - Show what would be done without changes
- `--force` - Skip confirmation prompts

**Examples:**
```bash
# Preview bridge creation
sudo clab-tools bridge create --dry-run

# Create bridges locally
sudo clab-tools bridge create

# Create bridges on remote host
clab-tools --enable-remote bridge create --force
```

#### `bridge create-bridge`

Create a single Linux bridge with custom options for manual bridge management.

```bash
sudo clab-tools bridge create-bridge BRIDGE_NAME [OPTIONS]
```

**Options:**
- `-i, --interface TEXT` - Physical interface to add to bridge (can be used multiple times)
- `--no-vlan-filtering` - Disable VLAN filtering on bridge
- `--stp` - Enable spanning tree protocol
- `--vid-range TEXT` - VLAN ID range to configure (default: 1-4094)
- `--dry-run` - Show what would be done without making changes

**Examples:**
```bash
# Create bridge with physical interface
sudo clab-tools bridge create-bridge br-mgmt --interface eth0

# Create access bridge without VLAN filtering
sudo clab-tools bridge create-bridge br-access --no-vlan-filtering --stp

# Create bridge with custom VLAN range
sudo clab-tools bridge create-bridge br-custom --vid-range 100-200

# Create bridge with multiple interfaces
sudo clab-tools bridge create-bridge br-trunk -i eth1 -i eth2

# Preview bridge creation
sudo clab-tools bridge create-bridge br-test --dry-run
```

#### `bridge list`

List bridge status and requirements.

```bash
clab-tools bridge list
```

Shows required bridges from topology and their current status.

#### `bridge configure`

Configure VLAN forwarding on bridge interfaces.

```bash
sudo clab-tools bridge configure [OPTIONS]
```

**Options:**
- `--bridge TEXT` - Target specific bridge (default: all bridges)
- `--dry-run` - Show what would be done without changes

**Examples:**
```bash
# Configure VLANs on all bridges
sudo clab-tools bridge configure

# Configure specific bridge
sudo clab-tools bridge configure --bridge br-access

# Preview VLAN configuration
sudo clab-tools bridge configure --dry-run
```

#### `bridge cleanup`

Delete Linux bridges from the system.

```bash
sudo clab-tools bridge cleanup [OPTIONS]
```

**Options:**
- `--dry-run` - Show what would be done without changes
- `--force` - Skip confirmation prompts

**Examples:**
```bash
# Preview bridge deletion
sudo clab-tools bridge cleanup --dry-run

# Delete bridges with confirmation
sudo clab-tools bridge cleanup

# Force delete without prompts
sudo clab-tools bridge cleanup --force
```

## Node Management

### `clab-tools node`

Manage individual containerlab nodes.

#### `node upload`

Upload files or directories to containerlab nodes using their management IP addresses.

```bash
clab-tools node upload [OPTIONS]
```

**Options:**
- `--node TEXT` - Upload to specific node
- `--kind TEXT` - Upload to all nodes of specific kind
- `--nodes TEXT` - Upload to comma-separated list of nodes
- `--all` - Upload to all nodes in current lab
- `--source PATH` - Local file to upload (required if not using --source-dir)
- `--source-dir PATH` - Local directory to upload recursively
- `--dest TEXT` - Remote destination path (required)
- `--user TEXT` - SSH username (overrides default)
- `--password TEXT` - SSH password (overrides default)
- `--private-key PATH` - SSH private key file (overrides default)

**Target Selection (choose one):**
- `--node` - Single node by name
- `--kind` - All nodes of a specific kind/type
- `--nodes` - Specific list of nodes
- `--all` - All nodes in the current lab

**Examples:**
```bash
# Upload file to specific node
clab-tools node upload --node router1 --source config.txt --dest /tmp/config.txt

# Upload to all SRX nodes
clab-tools node upload --kind srx --source juniper.conf --dest /etc/juniper.conf

# Upload to specific nodes
clab-tools node upload --nodes router1,router2,router3 --source config.yml --dest /tmp/config.yml

# Upload to all nodes in lab
clab-tools node upload --all --source startup.sh --dest /tmp/startup.sh

# Upload directory recursively
clab-tools node upload --node server1 --source-dir ./configs --dest /etc/configs

# Use custom credentials
clab-tools node upload --node switch1 --source config.txt --dest /tmp/config.txt \
  --user admin --password secret

# Use SSH key authentication
clab-tools node upload --kind linux --source script.sh --dest /opt/script.sh \
  --private-key ~/.ssh/lab_key

# Quiet mode for scripting
clab-tools --quiet node upload --all --source init.sh --dest /tmp/init.sh
```

**Upload Summary:**
After uploading, the command displays:
- Total nodes targeted
- Successful uploads
- Failed uploads
- Individual node results (unless in quiet mode)

#### `node exec`

Execute operational commands on network devices through vendor-specific drivers.

```bash
clab-tools node exec [OPTIONS]
```

**Options:**
- `-c, --command TEXT` - Command to execute (required)
- `--node TEXT` - Execute on specific node
- `--kind TEXT` - Execute on all nodes of specific kind
- `--nodes TEXT` - Execute on comma-separated list of nodes
- `--all` - Execute on all nodes in current lab (skips bridge nodes)
- `--parallel` - Execute commands in parallel
- `--max-workers INTEGER` - Maximum parallel workers (default: 5)
- `--timeout INTEGER` - Command timeout in seconds (default: 30)
- `--output-format [text|table|json]` - Output format (default: text)
- `--user TEXT` - SSH username (overrides default)
- `--password TEXT` - SSH password (overrides default)
- `--private-key PATH` - SSH private key file (overrides default)

**Target Selection (choose one):**
- `--node` - Single node by name
- `--kind` - All nodes of a specific kind/type
- `--nodes` - Specific list of nodes
- `--all` - All nodes in the current lab (automatically filters out bridge nodes)

**Output Formats:**
- `text` - Default format with node name headers and command output
- `table` - Tabular format for structured command output
- `json` - JSON format for programmatic processing

**Examples:**
```bash
# Execute command on single node
clab-tools node exec -c "show version" --node router1

# Execute on all Juniper vJunos routers
clab-tools node exec -c "show ospf neighbor" --kind juniper_vjunosrouter

# Execute on specific nodes with table output
clab-tools node exec -c "show interfaces terse" --nodes router1,router2 --output-format table

# Execute on all nodes in parallel (skips bridges)
clab-tools node exec -c "show system uptime" --all --parallel --max-workers 10

# Execute with custom timeout for long-running commands
clab-tools node exec -c "show configuration" --all --timeout 120

# Export results as JSON for processing
clab-tools node exec -c "show route summary" --all --output-format json > routes.json

# Use custom credentials
clab-tools node exec -c "show version" --node router1 --user admin --password secret

# Quiet mode for scripting
clab-tools --quiet node exec -c "show interfaces" --all --output-format json
```

**Features:**
- **Vendor-Agnostic**: Automatically detects and uses appropriate driver based on node vendor
- **Parallel Execution**: Run commands simultaneously across multiple nodes
- **Progress Tracking**: Rich progress bars show execution status (unless in quiet mode)
- **Error Handling**: Gracefully handles connection failures and command errors
- **Clean Output**: Suppresses verbose logging and warnings for professional output

**Currently Supported Vendors:**
- Juniper (all variants: vJunos, vMX, vSRX, vQFX, vEX)
- Additional vendors coming soon (Nokia SR Linux, Arista cEOS, Cisco IOS-XR)

#### `node config`

Load configurations to network devices through vendor-specific drivers.

```bash
clab-tools node config [OPTIONS]
```

**Options:**
- `-f, --file PATH` - Local configuration file to load
- `-d, --device-file TEXT` - Device file path to load configuration from
- `--node TEXT` - Load config on specific node
- `--kind TEXT` - Load config on all nodes of specific kind
- `--nodes TEXT` - Load config on comma-separated list of nodes
- `--all` - Load config on all nodes in current lab (skips bridge nodes)
- `--method [merge|override|replace]` - Configuration load method (default: merge)
- `--dry-run` - Validate configuration without applying
- `--diff` - Show configuration diff without applying
- `--rollback` - Rollback to previous configuration
- `--comment TEXT` - Commit comment for configuration change
- `--parallel` - Load configurations in parallel
- `--max-workers INTEGER` - Maximum parallel workers (default: 5)
- `--user TEXT` - SSH username (overrides default)
- `--password TEXT` - SSH password (overrides default)
- `--private-key PATH` - SSH private key file (overrides default)

**Configuration Sources (choose one):**
- `-f, --file` - Load configuration from local file
- `-d, --device-file` - Load configuration from file on device
- `--rollback` - Rollback to previous configuration (no file needed)

**Load Methods:**
- `merge` - Merge configuration with existing (default)
- `override` - Override specific configuration sections
- `replace` - Replace entire configuration

**Examples:**
```bash
# Load configuration from local file
clab-tools node config -f router.conf --node router1

# Load with dry-run to validate first
clab-tools node config -f baseline.conf --node router1 --dry-run

# Load configuration on all vMX routers with override method
clab-tools node config -f vmx-baseline.conf --kind juniper_vmx --method override

# Load from device file
clab-tools node config -d /tmp/device-config.txt --node router1

# Load on multiple nodes in parallel with comment
clab-tools node config -f ospf-update.conf --all --parallel --comment "OSPF area update"

# Show configuration diff before applying
clab-tools node config -f changes.conf --node router1 --diff

# Rollback configuration
clab-tools node config --rollback --node router1

# Load on specific nodes with merge method
clab-tools node config -f acl-update.conf --nodes router1,router2,router3 --method merge

# Use custom credentials
clab-tools node config -f secure.conf --node router1 --user admin --password secret

# Quiet mode for automation
clab-tools --quiet node config -f baseline.conf --all --parallel
```

**Features:**
- **Dual Source Support**: Load configurations from local files or device filesystem
- **Multiple Load Methods**: Support for merge, override, and replace operations
- **Dry-Run Validation**: Test configurations before applying them
- **Configuration Diff**: Preview changes before committing
- **Rollback Support**: Quickly revert to previous configuration
- **Parallel Loading**: Apply configurations to multiple nodes simultaneously
- **Progress Tracking**: Visual feedback during configuration operations
- **Automatic Format Detection**: Detects configuration format (set, text, XML, JSON)

**Configuration Formats:**
- **Set Format**: Commands starting with `set` or `delete`
- **Text Format**: Hierarchical bracketed format
- **XML Format**: JunOS XML configuration format
- **JSON Format**: JSON-based configuration format

**Safety Features:**
- Configuration validation before applying
- Automatic rollback on errors
- Configuration locking during operations
- Detailed error reporting
- Audit trail with commit comments

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

## Configuration Management

### `clab-tools config`

View and manage clab-tools configuration settings.

#### `config show`

Display current configuration settings and their sources (environment, file, or default).

```bash
clab-tools config show
```

**Options:**
- `-f, --format [tree|json|yaml]` - Output format (default: tree)
- `-s, --show-source / --no-show-source` - Show configuration source (default: true)
- `--section TEXT` - Show only a specific section

**Examples:**
```bash
# Show all settings with sources
clab-tools config show

# Show only remote configuration
clab-tools config show --section remote

# Export configuration as JSON
clab-tools config show --format json > config.json

# Show settings without source information
clab-tools config show --no-show-source

# Check database settings
clab-tools config show --section database

# Export as YAML for documentation
clab-tools config show --format yaml
```

**Output Format:**
- `[env]` - Value from environment variable
- `[file]` - Value from configuration file
- `[default]` - Default value

**Sections:**
- `database` - Database connection settings
- `logging` - Logging configuration
- `topology` - Topology generation defaults
- `lab` - Lab management settings
- `bridges` - Bridge management configuration
- `remote` - Remote host settings
- `node` - Node connection defaults
- `vendor` - Vendor-specific settings

#### `config env`

List all CLAB environment variables currently set.

```bash
clab-tools config env
```

**Examples:**
```bash
# Show all CLAB environment variables
clab-tools config env

# Common environment variables:
# CLAB_REMOTE_ENABLED=true
# CLAB_REMOTE_HOST=192.168.1.100
# CLAB_REMOTE_USERNAME=admin
# CLAB_DATABASE_URL=sqlite:///custom.db
# CLAB_LAB_CURRENT_LAB=production
# CLAB_LOG_ENABLED=false
# CLAB_LOG_LEVEL=DEBUG
```

**Note:** Sensitive values (passwords, keys) are masked with `****` in the output.

## Configuration Override Examples

### Lab-Specific Operations

```bash
# Work with specific lab without switching
clab-tools --lab production data show
clab-tools --lab staging data import -n staging.csv -c connections.csv

# Multiple overrides
clab-tools --config custom.yaml --lab special-env --debug topology generate -o lab.yml
```

### Remote Host Operations

```bash
# Using CLI flags for remote operations
clab-tools --remote-host 10.1.1.100 --remote-user admin --enable-remote bridge create

# Override remote credentials
clab-tools --remote-host 192.168.1.50 --remote-user clab --remote-password secret --enable-remote remote test-connection
```

### Database Override

```bash
# Use different database
clab-tools --db-url sqlite:///backup.db data show

# Temporary database for testing
clab-tools --db-url sqlite:///test.db data import -n test-nodes.csv -c test-connections.csv
```

### Debug Mode

```bash
# Enable debug logging
clab-tools --debug --log-level DEBUG topology generate -o lab.yml

# JSON logging format
clab-tools --log-format json --log-level INFO bridge create
```

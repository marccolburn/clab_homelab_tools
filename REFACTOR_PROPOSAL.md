# Clab-Tools Refactor Proposal

## Executive Summary

This proposal outlines a refactor to simplify the codebase, eliminate duplication, fix documentation inconsistencies, and prepare for future extensibility. The refactor will break existing commands in favor of a cleaner, more logical structure.

## Goals

1. **Eliminate code duplication** across commands and managers
2. **Simplify lab context management** by removing unnecessary wrapper layers
3. **Fix documentation** to match actual implementation
4. **Improve extensibility** for future features (config transfers, etc.)
5. **Create intuitive command structure** without legacy constraints

## Proposed Changes

### 1. Simplify Lab Context Management

**Current State**: Complex flow through LabAwareDB wrapper
**Proposed**: Direct lab-aware DatabaseManager

```python
# Before
db = get_lab_db(ctx.obj)  # Returns wrapper
lab = ctx.obj["current_lab"]  # Separate lab reference

# After
db = ctx.obj["db"]  # Direct access, already lab-aware
```

**Implementation**:
- Modify `DatabaseManager` to be lab-aware internally
- Remove `LabAwareDB` wrapper class
- Update all commands to use simplified context

### 2. Create Common Utilities Module

**New file**: `clab_tools/common/utils.py`

```python
# Command result handlers
def handle_success(message: str):
    click.echo(f"✓ {message}")

def handle_error(message: str, exit_code: int = 1):
    click.echo(f"✗ {message}", err=True)
    if exit_code:
        raise click.Abort()

# Common decorators
def with_lab_context(func):
    """Decorator that ensures lab context is available"""
    @functools.wraps(func)
    def wrapper(ctx, *args, **kwargs):
        if not ctx.obj.get("db"):
            raise click.ClickException("Database not initialized")
        return func(ctx, *args, **kwargs)
    return wrapper

# Remote operation helpers
def setup_remote_config(settings, **kwargs):
    """Unified remote configuration setup"""
    # Consolidate remote config logic
```

### 3. Reorganize Command Structure

**Current**: Flat command structure
**Proposed**: Grouped commands for better organization

```
clab-tools
├── lab
│   ├── create      # Create new lab
│   ├── switch      # Switch active lab
│   ├── delete      # Delete lab
│   └── list        # List all labs
├── data
│   ├── import      # Import from CSV
│   ├── export      # Export to CSV (new)
│   ├── show        # Show current data
│   └── clear       # Clear data
├── topology
│   ├── generate    # Generate topology YAML
│   └── validate    # Validate topology (new)
├── bridge
│   ├── create      # Create bridges
│   ├── configure   # Configure VLANs
│   ├── list        # List bridges
│   └── cleanup     # Remove bridges
└── remote
    ├── test        # Test connection
    ├── upload      # Upload topology
    └── execute     # Execute command
```

### 4. Consolidate Database Operations

**Create base patterns** in `DatabaseManager`:

```python
class DatabaseManager:
    def _execute_lab_operation(self, lab_name, operation, **kwargs):
        """Generic pattern for lab operations"""
        with self.get_session() as session:
            lab = self.get_or_create_lab(lab_name)
            result = operation(session, lab, **kwargs)
            self.logger.info(f"{operation.__name__} completed",
                           lab=lab_name, **result)
            return result

    # Simplified methods using the pattern
    def clear_nodes(self, lab_name=None):
        return self._execute_lab_operation(
            lab_name or self.current_lab,
            lambda session, lab: {
                "count": session.query(Node).filter_by(lab_id=lab.id).delete()
            }
        )
```

### 5. Fix Documentation

**Documentation updates**:
- Correct all command examples to match actual syntax
- Remove references to non-existent features
- Add missing command documentation
- Update CSV format specifications
- Create migration guide for users

### 6. Improve Bridge Management

**Current**: Only creates bridges from topology
**Proposed**: Support both topology-based and manual bridge management

```python
class BridgeManager:
    def create_bridge(self, name, **options):
        """Create individual bridge with options"""

    def create_topology_bridges(self):
        """Create all bridges from topology (current behavior)"""

    def create_bridge_from_spec(self, spec):
        """Create bridge from specification (for extensibility)"""
```

### 7. Prepare for Extensions

**Plugin system foundation**:

```python
# clab_tools/plugins/base.py
class BasePlugin:
    """Base class for clab-tools plugins"""
    def register_commands(self, cli):
        """Register plugin commands with CLI"""
        pass

# Future: Router config management plugin
class ConfigTransferPlugin(BasePlugin):
    def register_commands(self, cli):
        config_group = cli.group("config")
        config_group.command()(self.push_configs)
        config_group.command()(self.pull_configs)
```

## Implementation Plan

### Phase 1: Core Refactor (Branch: `refactor/simplify-core`)
1. Create common utilities module
2. Simplify DatabaseManager to be lab-aware
3. Remove LabAwareDB wrapper
4. Update all commands to use new patterns
5. Add comprehensive tests

### Phase 2: Command Reorganization (Branch: `refactor/command-structure`)
1. Implement command groups
2. Remove old command structure completely
3. Update documentation with new commands
4. Create shell script examples

### Phase 3: Bridge Enhancement (Branch: `feat/flexible-bridges`)
1. Refactor BridgeManager for flexibility
2. Add manual bridge creation commands
3. Update bridge documentation

### Phase 4: Documentation Update (Branch: `docs/accuracy-update`)
1. Fix all command examples
2. Update architecture documentation
3. Create migration guide
4. Update CLAUDE.md

## Testing Strategy

1. **Maintain existing tests** during refactor
2. **Add integration tests** for new patterns
3. **Mock bridge operations** for local development (since bridge creation requires root)
4. **Performance benchmarks** to ensure no regression
5. **Test shell script workflows** with example bootstrap.sh

## Shell Script Workflows

### Example bootstrap.sh for Lab Directory

```bash
#!/bin/bash
# bootstrap.sh - Initialize and deploy a containerlab topology

set -e  # Exit on error

# Configuration
LAB_NAME="datacenter-1"
REMOTE_HOST="192.168.1.100"
REMOTE_USER="clab"
TOPOLOGY_FILE="topology.yml"

echo "=== Containerlab Bootstrap Script ==="
echo "Lab: $LAB_NAME"
echo "Remote: $REMOTE_USER@$REMOTE_HOST"
echo ""

# 1. Create/switch to lab
echo "→ Setting up lab environment..."
clab-tools lab create $LAB_NAME || clab-tools lab switch $LAB_NAME

# 2. Import topology data
echo "→ Importing topology data..."
clab-tools data import \
    --nodes nodes.csv \
    --connections connections.csv

# 3. Show imported data for verification
echo "→ Verifying imported data..."
clab-tools data show

# 4. Generate topology file
echo "→ Generating topology file..."
clab-tools topology generate \
    --output $TOPOLOGY_FILE \
    --format yaml

# 5. Create bridges on remote host
echo "→ Creating bridges on remote host..."
clab-tools bridge create \
    --remote-host $REMOTE_HOST \
    --remote-user $REMOTE_USER

# 6. Configure VLANs if needed
if [ -f "vlans.csv" ]; then
    echo "→ Configuring VLANs..."
    clab-tools bridge configure \
        --remote-host $REMOTE_HOST \
        --remote-user $REMOTE_USER
fi

# 7. Upload topology to remote host
echo "→ Uploading topology file..."
clab-tools remote upload \
    --file $TOPOLOGY_FILE \
    --destination /home/$REMOTE_USER/labs/$LAB_NAME/ \
    --host $REMOTE_HOST \
    --username $REMOTE_USER

# 8. Deploy topology on remote host
echo "→ Deploying topology..."
clab-tools remote execute \
    --command "cd /home/$REMOTE_USER/labs/$LAB_NAME && sudo clab deploy -t $TOPOLOGY_FILE" \
    --host $REMOTE_HOST \
    --username $REMOTE_USER

echo ""
echo "✓ Deployment complete!"
echo "→ Access the lab at: ssh $REMOTE_USER@$REMOTE_HOST"
```

### Advanced Workflows

#### Multi-Lab Management
```bash
#!/bin/bash
# deploy-all-labs.sh - Deploy multiple labs to different hosts

LABS=(
    "lab1:192.168.1.100"
    "lab2:192.168.1.101"
    "lab3:192.168.1.102"
)

for lab_config in "${LABS[@]}"; do
    IFS=':' read -r lab host <<< "$lab_config"
    echo "Deploying $lab to $host..."

    clab-tools lab switch $lab
    clab-tools topology generate -o ${lab}.yml
    clab-tools bridge create --remote-host $host
    clab-tools remote upload -f ${lab}.yml -d /opt/clab/ -h $host
done
```

#### Backup and Restore
```bash
#!/bin/bash
# backup-lab.sh - Export lab data for backup

LAB_NAME=${1:-$(clab-tools lab current)}
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

mkdir -p $BACKUP_DIR

# Export all data
clab-tools data export \
    --nodes $BACKUP_DIR/nodes.csv \
    --connections $BACKUP_DIR/connections.csv \
    --vlans $BACKUP_DIR/vlans.csv

# Save current topology
clab-tools topology generate -o $BACKUP_DIR/topology.yml

# Create restore script
cat > $BACKUP_DIR/restore.sh << 'EOF'
#!/bin/bash
clab-tools lab create restored-$LAB_NAME
clab-tools data import -n nodes.csv -c connections.csv
[ -f vlans.csv ] && clab-tools data import -v vlans.csv
EOF

chmod +x $BACKUP_DIR/restore.sh
echo "✓ Backup saved to $BACKUP_DIR"
```

### Future Router Configuration Workflow (Post-Refactor)

The refactor will enable pushing configurations directly to containerized network nodes:

```bash
#!/bin/bash
# push-configs.sh - Push router configurations to containerized nodes

# Configuration would be pushed to individual node IPs, not the host
# The tool would:
# 1. Query the deployed topology for node management IPs
# 2. Connect to each node directly (via the host's network)
# 3. Push configurations using vendor-specific methods

# Example workflow after refactor:
clab-tools config push \
    --source configs/ \
    --nodes "spine*,leaf*" \
    --method scp  # or api, netconf, etc.

# The tool would resolve node IPs from the topology:
# spine1 -> 172.20.20.11 (management IP from containerlab)
# spine2 -> 172.20.20.12
# leaf1 -> 172.20.20.21
# etc.

# Or target specific nodes:
clab-tools config push \
    --source configs/spine1.cfg \
    --node spine1 \
    --ip 172.20.20.11  # Optional override

# Bulk operations with vendor-specific handling:
clab-tools config deploy \
    --template jinja2/base.j2 \
    --vars variables.yml \
    --vendor arista  # Handles EOS-specific deployment
```

## Benefits

1. **Reduced code**: ~30% less code through consolidation
2. **Simpler architecture**: Fewer layers and abstractions
3. **Better extensibility**: Plugin system for future features
4. **Improved UX**: Logical command grouping
5. **Accurate documentation**: Matches implementation
6. **Shell-friendly**: Designed for automation workflows
7. **Node-aware**: Foundation for direct node configuration management

## Timeline

- Phase 1: 2-3 days
- Phase 2: 1-2 days
- Phase 3: 1-2 days
- Phase 4: 1 day
- Testing & Review: 2 days

**Total**: ~1.5-2 weeks for complete refactor

## Next Steps

1. Review and approve this proposal
2. Create feature branch
3. Implement Phase 1
4. Create PR for review
5. Iterate through remaining phases

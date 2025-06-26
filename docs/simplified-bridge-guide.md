# Simplified Bridge Management Guide

## Overview

This guide explains the **simplified bridge approach** where bridges are treated as regular nodes and referenced directly in connections. All bridges are created with full VLAN support (VLANs 1-4094) for maximum flexibility.

## Key Concepts

### 1. Bridge Nodes
- Bridges are defined as nodes with `kind=bridge` in the nodes CSV
- Bridge nodes don't require `mgmt_ip` (automatically set to "N/A")
- All connections use `type=direct` - no special "bridge" connection type needed

### 2. Bridge Interface Naming Convention
Bridge interfaces follow the pattern: `eth{last_digit_of_node1_interface}{node_id}`

**Examples:**
- `r1` connecting via `ge-0/0/3` → last digit `3` + node ID `1` = `eth31`
- `r2` connecting via `ge-0/0/3` → last digit `3` + node ID `2` = `eth32`
- `r12` connecting via `ge-0/0/4` → last digit `4` + node ID `12` = `eth412`
- `r1` connecting via `fxp0` → last digit `0` + node ID `1` = `eth01`

### 3. VLAN Support
- All bridges are created with `vlan_filtering=1` enabled
- VLANs 1-4094 are pre-configured on each bridge
- Dynamic VLAN assignment when containers connect

## CSV File Format

### Nodes CSV
```csv
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
br-allvlans,bridge,
br-mgmt,bridge,
```

### Connections CSV
```csv
node1,node2,type,node1_interface,node2_interface
r1,r2,direct,ge-0/0/1,ge-0/0/1
r1,br-allvlans,direct,ge-0/0/3,eth31
r2,br-allvlans,direct,ge-0/0/3,eth32
r1,br-mgmt,direct,ge-0/0/4,eth41
r2,br-mgmt,direct,fxp0,eth01
```

## Bridge Interface Examples

| Node | Interface | Last Digit | Node ID | Bridge Interface |
|------|-----------|------------|---------|------------------|
| r1   | ge-0/0/3  | 3          | 1       | eth31           |
| r2   | ge-0/0/3  | 3          | 2       | eth32           |
| r10  | ge-0/0/4  | 4          | 10      | eth410          |
| r12  | ge-0/0/4  | 4          | 12      | eth412          |
| r1   | fxp0      | 0          | 1       | eth01           |
| sw5  | eth10     | 0          | 5       | eth05           |

## Usage Workflow

### 1. Create CSV Files
```bash
# Create nodes.csv with bridge nodes
cat > nodes.csv << EOF
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
br-access,bridge,
br-trunk,bridge,
br-mgmt,bridge,
EOF

# Create connections.csv with bridge references
cat > connections.csv << EOF
node1,node2,type,node1_interface,node2_interface
r1,r2,direct,ge-0/0/1,ge-0/0/1
r1,br-access,direct,ge-0/0/2,eth21
r2,br-access,direct,ge-0/0/2,eth22
r1,br-mgmt,direct,fxp0,eth01
r2,br-mgmt,direct,fxp0,eth02
EOF
```

### 2. Import Data
```bash
python -m clab_tools.main import-csv -n nodes.csv -c connections.csv --clear-existing
```

### 3. Create VLAN-Capable Bridges
```bash
# Preview what will be created
python -m clab_tools.main create-bridges --dry-run

# Create the bridges
python -m clab_tools.main create-bridges
```

### 4. Generate Topology
```bash
python -m clab_tools.main generate-topology -o lab.yml -t "my_lab"
```

## Bridge Creation Commands

When you run `create-bridges`, each bridge is created with these commands:

```bash
# Create bridge with VLAN filtering
ip link add name br-access type bridge vlan_filtering 1

# Bring bridge up
ip link set br-access up

# Add all VLANs 1-4094 to bridge
bridge vlan add vid 1-4094 dev br-access self
```

## VLAN Management

### Dynamic VLAN Assignment
Once containers are connected, you can assign VLANs dynamically:

```bash
# Add container interface to bridge
ip link set dev veth-r1-1 master br-access

# Assign access VLAN (untagged)
bridge vlan add vid 10 dev veth-r1-1 untagged pvid

# Configure trunk port (tagged VLANs)
bridge vlan add vid 10,20,30 dev veth-r1-2

# Add new VLANs as needed
bridge vlan add vid 100 dev br-access self
bridge vlan add vid 100 dev veth-r1-1 untagged
```

### Query VLAN Configuration
```bash
# Show all bridge VLANs
bridge vlan show

# Show specific bridge
bridge vlan show dev br-access

# Show VLAN on specific interface
bridge vlan show dev veth-r1-1
```

## Example Scenarios

### Scenario 1: Access Network
```csv
# nodes.csv
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
r3,juniper_vjunosrouter,10.100.100.13
br-access,bridge,

# connections.csv
node1,node2,type,node1_interface,node2_interface
r1,br-access,direct,ge-0/0/1,eth11
r2,br-access,direct,ge-0/0/1,eth12
r3,br-access,direct,ge-0/0/1,eth13
```

### Scenario 2: Multi-Bridge Topology
```csv
# nodes.csv
node_name,kind,mgmt_ip
r1,juniper_vjunosrouter,10.100.100.11
r2,juniper_vjunosrouter,10.100.100.12
sw1,arista_ceos,10.100.100.20
br-core,bridge,
br-edge,bridge,
br-mgmt,bridge,

# connections.csv
node1,node2,type,node1_interface,node2_interface
r1,br-core,direct,ge-0/0/1,eth11
r2,br-core,direct,ge-0/0/1,eth12
r1,br-edge,direct,ge-0/0/2,eth21
sw1,br-edge,direct,eth1,eth01
r1,br-mgmt,direct,fxp0,eth01
r2,br-mgmt,direct,fxp0,eth02
```

### Scenario 3: High-Density Topology
```csv
# Large topology with multiple routers
node1,node2,type,node1_interface,node2_interface
r1,br-backbone,direct,ge-0/0/0,eth01
r2,br-backbone,direct,ge-0/0/0,eth02
# ... up to ...
r99,br-backbone,direct,ge-0/0/0,eth099
```

## Benefits of This Approach

1. **Simplicity**: Everything is a direct connection, bridges are just nodes
2. **Consistency**: Same interface naming pattern across all bridges
3. **Scalability**: Supports any number of nodes and bridges
4. **VLAN Ready**: All bridges support full VLAN range (1-4094)
5. **Clear Topology**: Easy to understand bridge relationships
6. **Future-Proof**: Can add VLAN-specific logic later without changing core structure

## Migration from Old Approach

### Old CSV (bridge connection type):
```csv
node1,node2,type,node1_interface,node2_interface
r1,sw1,bridge,ge-0/0/3,eth1
r2,sw1,bridge,ge-0/0/3,eth2
```

### New CSV (bridge as node):
```csv
# Add bridge to nodes.csv
br-switch,bridge,

# Update connections.csv
r1,br-switch,direct,ge-0/0/3,eth31
r2,br-switch,direct,ge-0/0/3,eth32
```

This simplified approach provides maximum flexibility while maintaining clean, understandable topologies!

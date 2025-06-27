# CSV Format Specification

Data format specifications for importing network topology data.

## Nodes File Format

Defines network devices and bridge components.

### Required Columns

```csv
node_name,kind,mgmt_ip
```

### Column Specifications

- **`node_name`** (string, required): Unique identifier for the node
  - Must be unique within the lab
  - Used as containerlab node name
  - Alphanumeric and hyphens recommended

- **`kind`** (string, required): Containerlab node type
  - Common values: `juniper_vjunosrouter`, `arista_ceos`, `linux`
  - Special value: `bridge` for Linux bridge creation
  - See [supported kinds](../supported_kinds.yaml) for complete list

- **`mgmt_ip`** (string, optional): Management IP address
  - Required for non-bridge nodes
  - Leave empty for bridge nodes
  - Format: IPv4 address (e.g., `10.100.100.11`)

### Example Nodes File

```csv
node_name,kind,mgmt_ip
router1,juniper_vjunosrouter,10.100.100.11
router2,juniper_vjunosrouter,10.100.100.12
switch1,arista_ceos,10.100.100.21
switch2,arista_ceos,10.100.100.22
server1,linux,10.100.100.31
br-access,bridge,
br-core,bridge,
```

## Connections File Format

Defines links between network devices.

### Required Columns

```csv
node1,node2,type,node1_interface,node2_interface
```

### Column Specifications

- **`node1`** (string, required): First node name
  - Must exist in nodes file
  - Order doesn't matter (connections are bidirectional)

- **`node2`** (string, required): Second node name
  - Must exist in nodes file
  - Cannot be the same as node1

- **`type`** (string, required): Connection type
  - Currently only `direct` is supported
  - Future: `vlan`, `lag`, etc.

- **`node1_interface`** (string, required): Interface on first node
  - Device-specific naming (e.g., `ge-0/0/1`, `eth1`, `Ethernet1`)
  - Must be unique per node

- **`node2_interface`** (string, required): Interface on second node
  - Device-specific naming
  - Must be unique per node

### Example Connections File

```csv
node1,node2,type,node1_interface,node2_interface
router1,router2,direct,ge-0/0/1,ge-0/0/1
router1,switch1,direct,ge-0/0/2,Ethernet1
router2,switch2,direct,ge-0/0/2,Ethernet1
switch1,br-access,direct,Ethernet2,eth1
switch2,br-access,direct,Ethernet2,eth2
router1,br-core,direct,ge-0/0/0,eth1
router2,br-core,direct,ge-0/0/0,eth2
server1,br-access,direct,eth0,eth3
```

## Bridge Interface Naming

When connecting to bridge nodes, interface names follow these conventions:

### Device-to-Bridge Connections

- **Device side**: Use device-specific naming
  - Juniper: `ge-0/0/X`, `xe-0/0/X`
  - Arista: `Ethernet1`, `Ethernet2`
  - Linux: `eth0`, `eth1`

- **Bridge side**: Use `ethN` pattern
  - Start from `eth1` and increment
  - Keep consistent across your topology
  - Example: `eth1`, `eth2`, `eth3`

### Management Networks

For management connectivity, create a dedicated management bridge:

```csv
# Nodes
router1,juniper_vjunosrouter,10.100.100.11
router2,juniper_vjunosrouter,10.100.100.12
br-mgmt,bridge,

# Connections
router1,br-mgmt,direct,fxp0,eth1
router2,br-mgmt,direct,fxp0,eth2
```

## Validation Rules

### Node Validation

- Node names must be unique within a lab
- Bridge nodes cannot have management IPs
- Non-bridge nodes should have management IPs
- Node kinds must be supported by containerlab

### Connection Validation

- Both nodes must exist in nodes file
- Interface names must be unique per node
- Cannot connect node to itself
- Connection types must be valid

### Import Behavior

- **`--clear-existing`**: Removes all existing lab data before import
- **Default**: Appends to existing data (may cause conflicts)
- **Conflicts**: Duplicate node names or interface assignments will cause errors

## Complete Example

### nodes.csv
```csv
node_name,kind,mgmt_ip
pe1,juniper_vjunosrouter,10.100.100.11
pe2,juniper_vjunosrouter,10.100.100.12
p1,juniper_vjunosrouter,10.100.100.13
ce1,arista_ceos,10.100.100.21
ce2,arista_ceos,10.100.100.22
server1,linux,10.100.100.31
br-mgmt,bridge,
br-ce1,bridge,
br-ce2,bridge,
```

### connections.csv
```csv
node1,node2,type,node1_interface,node2_interface
pe1,p1,direct,ge-0/0/1,ge-0/0/1
pe2,p1,direct,ge-0/0/1,ge-0/0/2
pe1,br-ce1,direct,ge-0/0/2,eth1
pe2,br-ce2,direct,ge-0/0/2,eth1
ce1,br-ce1,direct,Ethernet1,eth2
ce2,br-ce2,direct,Ethernet1,eth2
server1,br-ce1,direct,eth0,eth3
pe1,br-mgmt,direct,fxp0,eth1
pe2,br-mgmt,direct,fxp0,eth2
p1,br-mgmt,direct,fxp0,eth3
ce1,br-mgmt,direct,Management1,eth4
ce2,br-mgmt,direct,Management1,eth5
server1,br-mgmt,direct,eth1,eth6
```

This example creates:
- MPLS core (PE1-P1-PE2)
- Customer connections via bridges
- Management network for all devices
- Server connected to CE1 site

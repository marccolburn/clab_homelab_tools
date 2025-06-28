# Implementation Plan for clab-tools Enhancements

## Overview
This document outlines the implementation plan for four main enhancements to the clab-tools project:

1. **Non-interactive mode for all commands** - Add support for scripting by avoiding prompts
2. **New start/stop commands** - Simplified commands for starting/stopping containerlab topologies
3. **Node file upload capability** - Upload files directly to containerlab nodes using management IPs
4. **Bootstrap/teardown commands** - Automate complete lab setup and cleanup workflows

## Task 1: Non-interactive Mode for All Commands

### Requirements
- All commands should support a `--quiet` or `--non-interactive` flag to suppress prompts
- The `lab create` command currently auto-prompts to switch labs - this needs to be suppressible
- Maintain backward compatibility with existing behavior

### Implementation Details
1. Add a global `--quiet` option to the main CLI group
2. Update `lab create` command to check for quiet mode before prompting
3. Review all other commands for interactive prompts and update accordingly
4. Ensure all prompts have a non-interactive alternative

### Files to Modify
- `clab_tools/main.py` - Add global quiet option
- `clab_tools/commands/lab_commands.py` - Update lab create command
- `clab_tools/commands/data_commands.py` - Update clear command (already has --force)
- `clab_tools/commands/remote_commands.py` - Review password prompts

## Task 2: New Start/Stop Commands

### Requirements
- Create new commands: `clab-tools start` and `clab-tools stop`
- Default to local execution (remote only when configured/specified)
- Use `remote.topology_remote_dir` setting only when remote is enabled
- Allow custom path override
- Handle topology file specification

### Command Structure
```bash
# Start topology locally (default behavior)
clab-tools start topology.yml

# Start with custom path
clab-tools start topology.yml --path /custom/path

# Stop topology locally
clab-tools stop topology.yml

# Force remote execution
clab-tools start topology.yml --remote

# Force local execution (when remote is configured)
clab-tools start topology.yml --local
```

### Implementation Details
1. Add start/stop commands to topology command group
2. Implement start command:
   - Default to local execution
   - If remote is configured/requested:
     - Build full path using remote.topology_remote_dir or custom path
     - Execute via remote: `clab deploy -t <full_path>`
   - For local execution:
     - Use current directory or custom path
     - Execute locally: `clab deploy -t <full_path>`
3. Implement stop command:
   - Similar logic but execute `clab destroy -t <full_path>`
4. Add appropriate error handling and output

### Files to Create/Modify
- `clab_tools/commands/topology_commands.py` - Add start/stop commands (update existing generate command file)
- `clab_tools/config/settings.py` - Add topology_remote_dir to RemoteHostSettings
- `config.yaml` - Add default topology_remote_dir
- `config.local.example.yaml` - Add example

## Task 3: Node File Upload Capability

### Requirements
- Upload files to individual containerlab nodes (not just the host)
- Use node management IPs from the database
- Support configurable node credentials (username/password)
- Add new settings for node authentication
- Use keyword arguments instead of positional arguments
- Support uploading by node kind, group of nodes, or all nodes in lab
- Support uploading entire folders

### Command Structure
```bash
# Upload file to specific node
clab-tools node upload --node <node_name> --source <local_file> --dest <remote_path>

# Upload to all nodes in current lab
clab-tools node upload --all --source <local_file> --dest <remote_path>

# Upload to multiple nodes by kind
clab-tools node upload --kind srx --source <local_file> --dest <remote_path>

# Upload to group of nodes
clab-tools node upload --nodes node1,node2,node3 --source <local_file> --dest <remote_path>

# Upload entire folder
clab-tools node upload --node <node_name> --source-dir <local_folder> --dest <remote_path>

# Use custom credentials
clab-tools node upload --node <node_name> --source <local_file> --dest <remote_path> --user admin --password secret
```

### Implementation Details
1. Create new node commands subgroup
2. Add NodeSettings to configuration:
   - Default username
   - Default password (with security considerations)
   - SSH port
   - Connection timeout
3. Implement upload command:
   - Query database for node management IP(s)
   - Create SSH connection to node (through remote host if configured)
   - Support single file upload via SFTP
   - Support folder upload with recursive copy
   - Support bulk operations by node kind, node list, or all nodes
4. Add progress indicators for large transfers
5. Handle connection failures gracefully with retry logic

### Files to Create/Modify
- `clab_tools/commands/node_commands.py` - New command module
- `clab_tools/config/settings.py` - Add NodeSettings class
- `clab_tools/node/` - New module for node operations
- `config.yaml` - Add node settings section
- `config.local.example.yaml` - Add example with security warnings

## Task 4: Bootstrap and Teardown Commands

### Requirements
- Replace manual bootstrap.sh and teardown.sh scripts with native commands
- Support the complete lab lifecycle from CSV import to running topology
- Maintain flexibility for custom workflows
- Use current command syntax (not legacy syntax from scripts)

### Command Structure
```bash
# Bootstrap a complete lab
clab-tools lab bootstrap --nodes nodes.csv --connections connections.csv --output topology.yml

# Teardown a lab
clab-tools lab teardown --topology topology.yml

# Bootstrap with custom options
clab-tools lab bootstrap --nodes nodes.csv --connections connections.csv --output topology.yml --no-start --skip-vlans
```

### Bootstrap Workflow
1. Import CSV data (with --force to clear existing)
2. Generate topology file with validation
3. Upload topology to remote host (if remote configured)
4. Create bridges
5. Start containerlab topology
6. Configure VLANs on bridge interfaces

### Teardown Workflow
1. Stop containerlab topology
2. Remove bridges
3. Optional: Clear database entries

### Implementation Details
1. Add bootstrap command:
   ```python
   # Workflow steps
   - Import CSV: `clab-tools data import -n nodes.csv -c connections.csv --force`
   - Generate: `clab-tools topology generate -o topology.yml --validate`
   - Upload (if remote): automatic based on configuration
   - Create bridges: `clab-tools bridge create`
   - Start: `clab-tools start topology.yml`
   - Configure VLANs: `clab-tools bridge configure`
   ```
2. Add teardown command:
   ```python
   # Workflow steps
   - Stop: `clab-tools stop topology.yml`
   - Delete bridges: `clab-tools bridge cleanup`
   - Optional: Clear data
   ```
3. Support options to skip specific steps
4. Add dry-run mode to preview actions

### Files to Create/Modify
- `clab_tools/commands/lab_commands.py` - Add bootstrap/teardown commands
- Documentation updates for new workflow commands

## Documentation Updates

### Files to Update
1. `docs/commands.md` - Add new commands and options
2. `docs/user-guide.md` - Add examples for new functionality
3. `docs/getting-started.md` - Update with new capabilities
4. `README.md` - Mention new features in overview

### Key Documentation Points
- Explain quiet/non-interactive mode for scripting
- Provide examples of start/stop commands
- Document node upload with security best practices
- Show complete bootstrap/teardown workflows
- Update configuration examples

## Testing Strategy

### New Test Files
1. `tests/test_quiet_mode.py` - Test non-interactive behavior
2. `tests/test_start_stop_commands.py` - Test topology lifecycle commands
3. `tests/test_node_upload.py` - Test node file upload functionality
4. `tests/test_bootstrap_teardown.py` - Test complete workflows

### Test Scenarios
- Verify quiet mode suppresses all prompts
- Test start/stop with default and custom paths
- Test node upload with various authentication methods
- Test folder upload functionality
- Test upload to all nodes in lab
- Verify error handling for invalid nodes/paths
- Test bulk operations by node kind and node groups
- Test complete bootstrap and teardown workflows

## Security Considerations

### Node Credentials
- Store passwords securely (consider using keyring or environment variables)
- Document security best practices
- Support SSH key authentication where possible
- Warn about plaintext passwords in config files

### File Upload
- Validate file paths to prevent directory traversal
- Limit file sizes if necessary
- Log all upload operations
- Support secure protocols only (SSH/SFTP)

## Implementation Order

1. **Phase 1: Non-interactive Mode**
   - Implement global quiet option
   - Update existing commands
   - Test scripting scenarios

2. **Phase 2: Start/Stop Commands**
   - Add configuration for topology_remote_dir
   - Implement commands with local-first behavior
   - Test local and remote execution

3. **Phase 3: Node Upload**
   - Design node authentication system
   - Implement upload functionality with keyword args
   - Add folder and bulk upload support (including --all option)
   - Add security measures
   - Document best practices

4. **Phase 4: Bootstrap/Teardown**
   - Implement workflow commands
   - Add options for customization
   - Test complete lab lifecycle

## Success Criteria

- All commands can run without user interaction when --quiet is specified
- Start/stop commands work locally by default, remote when configured
- Node upload supports files, folders, and bulk operations with keyword args (including --all)
- Bootstrap/teardown commands replace manual scripts effectively
- Documentation is comprehensive and includes examples
- All tests pass and maintain existing functionality
- Security best practices are followed and documented

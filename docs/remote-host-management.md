# Remote Host Management

This document describes the remote host management capabilities of the clab-homelab-tools package, allowing you to run containerlab operations on remote hosts.

## Overview

The remote host management feature enables you to:

- Connect to remote containerlab hosts via SSH/SFTP
- Execute bridge management commands on remote hosts
- Upload topology files to remote hosts
- Run arbitrary commands on remote hosts
- Manage remote host credentials securely

## Configuration

Remote host settings can be configured through multiple methods (in order of precedence):

1. Command-line arguments
2. Environment variables
3. Configuration files
4. Default values

### Configuration File

Add a `remote` section to your YAML configuration file:

```yaml
remote:
  enabled: true
  host: "192.168.1.100"
  username: "clab-user"
  password: "secure-password"  # Optional if using key authentication
  private_key_path: "~/.ssh/id_rsa"  # Optional if using password authentication
  port: 22
  topology_remote_dir: "/tmp/clab-topologies"
  timeout: 30
```

### Environment Variables

Configure remote host settings using environment variables:

```bash
export CLAB_REMOTE_ENABLED=true
export CLAB_REMOTE_HOST=192.168.1.100
export CLAB_REMOTE_USERNAME=clab-user
export CLAB_REMOTE_PASSWORD=secure-password
export CLAB_REMOTE_PORT=22
export CLAB_REMOTE_PRIVATE_KEY_PATH=~/.ssh/id_rsa
export CLAB_REMOTE_TOPOLOGY_REMOTE_DIR=/tmp/clab-topologies
export CLAB_REMOTE_TIMEOUT=30
```

### Command Line Arguments

Override settings directly via command-line arguments:

```bash
clab-tools --remote-host 192.168.1.100 --remote-user clab-user --enable-remote generate-topology --upload
```

Available CLI options:
- `--remote-host` - Remote host IP or hostname
- `--remote-user` - Remote host username
- `--remote-password` - Remote host password
- `--remote-port` - SSH port (default: 22)
- `--remote-key` - Path to SSH private key file
- `--enable-remote` - Enable remote operations

## Authentication Methods

### Password Authentication

```yaml
remote:
  enabled: true
  host: "192.168.1.100"
  username: "clab-user"
  password: "secure-password"
```

### SSH Key Authentication

```yaml
remote:
  enabled: true
  host: "192.168.1.100"
  username: "clab-user"
  private_key_path: "~/.ssh/id_rsa"
```

### Security Considerations

1. **SSH Key Authentication** (Recommended): More secure than password authentication
2. **Environment Variables**: Avoid storing passwords in configuration files
3. **File Permissions**: Ensure configuration files have appropriate permissions (600)
4. **SSH Agent**: Consider using SSH agent for key management
5. **Host Key Verification**: The tool currently uses `AutoAddPolicy` for convenience, but consider manual host key verification for production

## Usage Examples

### Basic Remote Configuration Test

```bash
# Test remote host connection
clab-tools remote-test --remote-host 192.168.1.100 --remote-user clab-user --enable-remote

# Show current remote configuration
clab-tools remote-config
```

### Bridge Management on Remote Host

```bash
# Create bridges on remote host
clab-tools --enable-remote create-bridges

# List bridge status on remote host
clab-tools --enable-remote list-bridges

# Delete bridges on remote host
clab-tools --enable-remote delete-bridges
```

### Topology Generation with Remote Upload

```bash
# Generate topology and upload to remote host
clab-tools generate-topology --upload --remote-host 192.168.1.100 --enable-remote

# Generate with custom output and upload
clab-tools generate-topology -o my-lab.yml --upload --enable-remote
```

### File Operations

```bash
# Upload a file to remote host
clab-tools remote-upload /local/path/topology.yml /remote/path/topology.yml

# Execute command on remote host
clab-tools remote-exec "clab deploy -t /tmp/clab-topologies/topology.yml"
```

## CLI Commands

### Remote-Specific Commands

#### `remote-test`
Test connection to remote host.

```bash
clab-tools remote-test [OPTIONS]
```

#### `remote-config`
Display current remote host configuration.

```bash
clab-tools remote-config
```

#### `remote-upload`
Upload files to remote host.

```bash
clab-tools remote-upload [OPTIONS] LOCAL_PATH REMOTE_PATH
```

Options:
- `--create-dirs` - Create remote directories if they don't exist

#### `remote-exec`
Execute commands on remote host.

```bash
clab-tools remote-exec [OPTIONS] COMMAND
```

Options:
- `--dry-run` - Show what would be executed without running

### Modified Existing Commands

All bridge management commands now support remote operation when remote host is configured:

- `create-bridges` - Create bridges on local or remote host
- `delete-bridges` - Delete bridges on local or remote host
- `list-bridges` - List bridges on local or remote host

The `generate-topology` command has a new `--upload` option to automatically upload generated topology files to the remote host.

## Error Handling

The tool provides comprehensive error handling for remote operations:

### Connection Errors
- SSH connection failures
- Authentication failures
- Network timeouts
- Host key verification issues

### Command Execution Errors
- Remote command failures
- Permission issues
- File not found errors

### File Transfer Errors
- SFTP connection issues
- Disk space problems
- Permission denied errors

## Troubleshooting

### Common Issues

#### "Remote host operations are not enabled"
- Ensure `enabled: true` in configuration or use `--enable-remote`
- Verify host and username are configured

#### "No authentication method configured"
- Provide either password or private key path
- Check file permissions on private key files

#### "Connection failed"
- Verify host is reachable: `ping <remote-host>`
- Check SSH service is running: `ssh <user>@<host>`
- Verify firewall rules allow SSH connections
- Check SSH port configuration

#### "Permission denied"
- Verify username and password/key are correct
- Check if user has sudo privileges for bridge commands
- Ensure private key file permissions are 600

#### "Command failed with exit code"
- Check remote host has required tools installed (ip, bridge commands)
- Verify user has necessary privileges
- Check if containerlab is installed on remote host

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
clab-tools --debug --log-level DEBUG remote-test
```

### Manual SSH Testing

Test SSH connectivity manually:

```bash
# Test basic SSH connection
ssh user@remote-host

# Test command execution
ssh user@remote-host "ip link show"

# Test SFTP connection
sftp user@remote-host
```

## Integration with Containerlab

### Typical Workflow

1. **Configure remote host** with containerlab installed
2. **Generate topology** locally with database
3. **Upload topology** to remote host
4. **Create bridges** on remote host
5. **Deploy containerlab** on remote host

Example complete workflow:

```bash
# Import network design
clab-tools import-csv nodes.csv connections.csv

# Generate and upload topology
clab-tools generate-topology --upload --enable-remote

# Create required bridges on remote host
clab-tools create-bridges --enable-remote

# Deploy containerlab on remote host
clab-tools remote-exec "clab deploy -t /tmp/clab-topologies/clab.yml"
```

### Remote Host Requirements

The remote host should have:

1. **SSH server** running and accessible
2. **Containerlab** installed
3. **Bridge utilities** (bridge-utils package)
4. **iproute2** package for ip commands
5. **Sudo privileges** for the remote user (for bridge operations)
6. **Python 3.7+** if running Python-based tools

### Remote Directory Structure

Default directory structure on remote host:

```
/tmp/clab-topologies/           # Topology files
├── clab.yml                    # Generated topology
├── backup/                     # Backup topologies
└── logs/                       # Operation logs
```

## API Reference

### RemoteHostManager Class

The core class for managing remote host connections:

```python
from clab_tools.remote import RemoteHostManager
from clab_tools.config.settings import RemoteHostSettings

# Create settings
settings = RemoteHostSettings(
    enabled=True,
    host="192.168.1.100",
    username="user",
    password="pass"
)

# Use as context manager
with RemoteHostManager(settings) as manager:
    # Execute command
    exit_code, stdout, stderr = manager.execute_command("ls -la")

    # Upload file
    manager.upload_file("/local/file", "/remote/file")

    # Upload topology
    remote_path = manager.upload_topology_file("/local/topology.yml")
```

### Factory Function

```python
from clab_tools.remote import get_remote_host_manager

# Get manager based on global settings
manager = get_remote_host_manager()
if manager:
    with manager:
        # Perform remote operations
        pass
```

### Decorator

```python
from clab_tools.remote import with_remote_host

@with_remote_host
def my_function(remote_manager=None):
    if remote_manager:
        # Remote operation
        remote_manager.execute_command("echo 'remote'")
    else:
        # Local operation
        print("local")
```

## Best Practices

1. **Use SSH keys** instead of passwords for authentication
2. **Test connectivity** before running complex operations
3. **Use dry-run mode** to preview operations
4. **Monitor disk space** on remote host for topology files
5. **Keep backups** of important topology files
6. **Use specific remote directories** to avoid conflicts
7. **Validate topology files** before uploading
8. **Use timeouts** appropriate for your network latency
9. **Configure proper logging** for troubleshooting
10. **Secure your credentials** using environment variables or secure storage

## Future Enhancements

Planned improvements include:

- SSH agent support
- Multiple remote host support
- Encrypted credential storage
- SSH tunneling support
- Batch operations
- Remote host discovery
- Configuration templates
- Remote monitoring and health checks

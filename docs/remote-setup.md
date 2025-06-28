# Remote Host Setup

Configure and use remote containerlab hosts for topology deployment.

## Prerequisites

### Remote Host Requirements

- Linux system with containerlab installed
- SSH server running
- User account with sudo privileges for containerlab commands
- Docker/Podman runtime for container images

### Network Access

- SSH connectivity from local machine to remote host
- Container image access (Docker Hub, registry)
- Adequate storage for container images and lab files

## Configuration Methods

### Method 1: Configuration File

Create or edit `config.yaml`:

```yaml
remote:
  enabled: true
  host: "192.168.1.100"
  username: "clab-user"
  port: 22
  # Choose authentication method:
  password: "your-password"
  # OR
  private_key_path: "~/.ssh/id_rsa"
  # Optional sudo configuration:
  use_sudo: true
  sudo_password: "sudo-password"  # If different from login password
```

### Method 2: Environment Variables

```bash
export CLAB_REMOTE_ENABLED=true
export CLAB_REMOTE_HOST=192.168.1.100
export CLAB_REMOTE_USERNAME=clab-user
export CLAB_REMOTE_PASSWORD=your-password
# OR
export CLAB_REMOTE_PRIVATE_KEY_PATH=~/.ssh/id_rsa
```

### Method 3: CLI Arguments

```bash
clab-tools --remote-host 192.168.1.100 --remote-user clab-user --enable-remote [command]
```

## Authentication Setup

### SSH Key Authentication (Recommended)

```bash
# Generate SSH key pair (if not exists)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/clab_rsa

# Copy public key to remote host
ssh-copy-id -i ~/.ssh/clab_rsa.pub clab-user@192.168.1.100

# Test SSH connection
ssh -i ~/.ssh/clab_rsa clab-user@192.168.1.100

# Configure clab-tools
clab-tools --remote-host 192.168.1.100 --remote-user clab-user --remote-key ~/.ssh/clab_rsa --enable-remote remote test-connection
```

### Password Authentication

```bash
# Test connection with password
clab-tools --remote-host 192.168.1.100 --remote-user clab-user --remote-password your-password --enable-remote remote test-connection
```

## Remote Host Preparation

### Containerlab Installation

Ensure containerlab is installed on remote host:

```bash
# Test remote containerlab installation
clab-tools --enable-remote remote execute "clab version"

# If not installed, install containerlab:
clab-tools --enable-remote remote execute "bash -c \"$(curl -sL https://get.containerlab.dev)\""
```

### Directory Structure

clab-tools creates directories on remote host:

```
/tmp/clab-topologies/    # Topology files
/tmp/clab-uploads/       # Temporary uploads
```

### Sudo Configuration

For containerlab operations requiring root:

```bash
# Test sudo access
clab-tools --enable-remote remote execute "sudo clab version"

# Configure passwordless sudo (optional)
echo "clab-user ALL=(ALL) NOPASSWD: /usr/bin/clab" | sudo tee /etc/sudoers.d/clab-user
```

## Usage Workflows

### Basic Remote Operations

```bash
# Test connection
clab-tools --enable-remote remote test-connection

# View current configuration
clab-tools remote show-config

# Execute commands
clab-tools --enable-remote remote execute "pwd"
clab-tools --enable-remote remote execute "clab version"
```

### Remote Topology Deployment

```bash
# Generate and upload topology
clab-tools topology generate --upload --enable-remote -o lab.yml

# Create bridges on remote host
clab-tools --enable-remote bridge create

# Start topology using simplified command (uses topology_remote_dir)
clab-tools topology start lab.yml --remote

# Monitor deployment
clab-tools --enable-remote remote execute "clab inspect"

# Stop topology
clab-tools topology stop lab.yml --remote

# Cleanup bridges
clab-tools --enable-remote bridge cleanup
```

### Start/Stop Commands with Remote Host

The new start/stop commands simplify remote operations:

```bash
# Start topology on remote host (uses remote.topology_remote_dir setting)
clab-tools topology start lab.yml --remote

# Start with custom path on remote
clab-tools topology start lab.yml --remote --path /home/clab-user/topologies/lab.yml

# Force local execution even when remote is configured
clab-tools --enable-remote topology start lab.yml --local

# Stop topology on remote
clab-tools topology stop lab.yml --remote
```

### File Management

```bash
# Upload topology file
clab-tools --enable-remote remote upload-topology my-lab.yml

# Execute with uploaded file
clab-tools --enable-remote remote execute "sudo clab deploy -t /tmp/clab-topologies/my-lab.yml"
```

### Node File Upload

Upload files directly to containerlab nodes through the remote host:

```bash
# Upload config to specific node (SSH through remote host to node)
clab-tools node upload --node router1 --source config.txt --dest /tmp/config.txt

# Upload to all nodes (works with local or remote topologies)
clab-tools node upload --all --source startup.sh --dest /tmp/startup.sh

# Upload with custom credentials
clab-tools node upload --node switch1 --source config.cfg --dest /etc/config.cfg \
  --user admin --password secret
```

**Note**: Node uploads work whether your topology is running locally or on a remote host. The tool automatically handles SSH connectivity through the appropriate path.

## Troubleshooting

### Connection Issues

```bash
# Test basic SSH connectivity
ssh clab-user@192.168.1.100

# Test with specific key
ssh -i ~/.ssh/clab_rsa clab-user@192.168.1.100

# Debug SSH connection
ssh -v clab-user@192.168.1.100
```

### Authentication Problems

```bash
# Verify SSH key permissions
chmod 600 ~/.ssh/clab_rsa
chmod 644 ~/.ssh/clab_rsa.pub

# Check authorized_keys on remote host
cat ~/.ssh/authorized_keys
```

### Sudo Issues

```bash
# Test sudo without password
clab-tools --enable-remote remote execute "sudo -n true"

# Test sudo with password prompt
clab-tools --enable-remote remote execute "sudo true"
```

### Containerlab Issues

```bash
# Check containerlab installation
clab-tools --enable-remote remote execute "which clab"
clab-tools --enable-remote remote execute "clab version"

# Check Docker/container runtime
clab-tools --enable-remote remote execute "docker version"
clab-tools --enable-remote remote execute "sudo docker version"
```

## Security Considerations

### SSH Security

- Use SSH key authentication instead of passwords
- Limit SSH access to specific IP ranges
- Consider using SSH bastion hosts for production
- Regularly rotate SSH keys

### User Privileges

- Create dedicated user for clab-tools operations
- Limit sudo access to containerlab commands only
- Use passwordless sudo carefully (security vs convenience)

### Network Security

- Ensure remote host is on trusted network
- Consider VPN access for remote operations
- Monitor SSH access logs
- Use firewall rules to restrict access

## Bootstrap and Teardown on Remote Hosts

The bootstrap and teardown commands work seamlessly with remote hosts:

```bash
# Bootstrap complete lab on remote host
clab-tools --enable-remote lab bootstrap -n nodes.csv -c connections.csv -o lab.yml

# Teardown remote lab
clab-tools --enable-remote lab teardown -t lab.yml

# Non-interactive remote bootstrap for automation
clab-tools --quiet --enable-remote lab bootstrap -n nodes.csv -c connections.csv -o lab.yml
```

## Example Configuration

### Complete config.yaml

```yaml
# Database settings
database:
  # url: "sqlite:///custom_path.db"  # Uncomment to override default project directory location

# Lab settings
lab:
  current_lab: "production"

# Topology settings
topology:
  default_name: "homelab"
  default_prefix: ""

# Remote host configuration
remote:
  enabled: true
  host: "192.168.1.100"
  port: 22
  username: "clab-user"
  private_key_path: "~/.ssh/clab_rsa"
  use_sudo: true
  # Optional: sudo_password if different from login password
  topology_remote_dir: "/tmp/clab-topologies"  # Directory for topology files on remote host

# Node settings for SSH access to containerlab nodes
node:
  default_username: "admin"
  private_key_path: "~/.ssh/node_key"
  ssh_port: 22
  connection_timeout: 30

# Logging settings
logging:
  level: "INFO"
  format: "console"
```

### Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAB_REMOTE_ENABLED=true
export CLAB_REMOTE_HOST=192.168.1.100
export CLAB_REMOTE_USERNAME=clab-user
export CLAB_REMOTE_PRIVATE_KEY_PATH=~/.ssh/clab_rsa
```

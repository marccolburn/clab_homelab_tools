# Containerlab Homelab Tools

A multi-lab CLI tool for managing containerlab network topologies with persistent storage and remote host support.

## Quick Start

```bash
# Setup
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools
./install-cli.sh

# Bootstrap a complete lab (new!)
clab-tools lab bootstrap --nodes nodes.csv --connections connections.csv --output lab.yml

# Or step-by-step:
clab-tools lab create my-lab
clab-tools data import -n nodes.csv -c connections.csv
clab-tools topology generate -o lab.yml
sudo clab-tools bridge create
clab-tools topology start lab.yml
```

## Key Features

- **Multi-Lab Management**: Isolated environments for different topology projects
- **CSV Import/Export**: Simple data format for network topology definitions
- **Remote Host Support**: Deploy and manage topologies on remote containerlab hosts
- **Bridge Management**: Automated and manual Linux bridge creation with VLAN support
- **Configuration Flexibility**: YAML files, environment variables, and CLI overrides
- **Non-Interactive Mode**: Global `--quiet` flag for scripting and automation
- **Node File Upload**: Upload files and directories directly to containerlab nodes
- **Lab Lifecycle Commands**: Bootstrap and teardown complete lab environments with single commands

## Documentation

📖 **Core Documentation**
- [Getting Started](docs/getting-started.md) - Installation and first steps
- [User Guide](docs/user-guide.md) - Complete usage guide with examples
- [Command Reference](docs/commands.md) - All CLI commands and options

🔧 **Advanced Topics**
- [Remote Host Setup](docs/remote-setup.md) - Configure remote containerlab hosts
- [Configuration](docs/configuration.md) - Settings and customization
- [Development](docs/development.md) - Contributing and development setup

🔍 **Reference**
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [CSV Format](docs/csv-format.md) - Data format specifications

## Architecture

```
clab-tools
├── Multi-Lab Database (SQLite)
├── CLI Commands
│   ├── lab (create/switch/delete/bootstrap/teardown)
│   ├── data (import/show/clear)
│   ├── topology (generate/start/stop)
│   ├── bridge (create/create-bridge/configure/list/cleanup)
│   ├── node (upload)
│   └── remote (execute/upload/test)
├── Local & Remote Deployment
└── Configuration Management
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See the [Development Guide](docs/development.md) for setup instructions and contribution guidelines.

```bash
# Quick start for contributors
./scripts/setup-dev.sh
git checkout -b feature/your-feature
# Make changes, test, commit, push, create PR
```

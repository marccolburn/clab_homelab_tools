# Containerlab Homelab Tools

A comprehensive CLI utility for managing containerlab network topologies with persistent storage, structured logging, and professional error handling.

## Features

- **CSV Import**: Import node and connection data from CSV files
- **Topology Generation**: Generate containerlab YAML files from database data
- **Bridge Management**: Create and manage Linux bridges on the host system
- **Configuration Management**: YAML config files and environment variables
- **Structured Logging**: Professional logging with Rich console output
- **Database Storage**: SQLAlchemy-based persistent storage
- **Type Safety**: Full type hints and comprehensive testing

## Quick Start

```bash
# Clone and setup
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Basic usage
python main.py import-csv -n example_nodes.csv -c example_connections.csv
python main.py generate-topology -o my_lab.yml

# Optional: Install system-wide CLI
./install-cli.sh
clab-tools --help  # Use from anywhere
```

## Documentation

- 🎯 **[Project Workflows & Architecture](docs/workflows-and-architecture.md)** - **START HERE** for clear workflow diagrams
- 📖 **[Installation Guide](docs/installation.md)** - Setup and system-wide CLI installation
- 🎯 **[User Guide](docs/user-guide.md)** - Complete usage instructions and workflows
- ⚙️ **[Configuration](docs/configuration.md)** - Settings and customization options
- 🏗️ **[Developer Guide](docs/developer-guide.md)** - Development setup and testing
- 🔄 **[Development Workflow](docs/development-workflow.md)** - Git workflow, CI/CD, and contribution process
- 🏛️ **[Architecture](docs/architecture.md)** - Project structure and design
- 🐛 **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- 📚 **[API Reference](docs/api-reference.md)** - CLI commands and options
- 🔗 **[Quick Reference](QUICK_REFERENCE.md)** - Command summary

## Basic Commands

```bash
# Import data from CSV files
python main.py import-csv -n nodes.csv -c connections.csv

# View imported data
python main.py show-data

# Generate containerlab topology
python main.py generate-topology -o lab.yml

# Create host bridges (requires root)
sudo python main.py create-bridges
```

For detailed usage instructions, see the [User Guide](docs/user-guide.md).

## Contributing

We follow a trunk-based development model. See the [Development Workflow Guide](docs/development-workflow.md) for detailed instructions on:
- Setting up your development environment
- Pre-commit hooks and code quality
- Testing and CI/CD process
- Pull request workflow
- Release process

Quick start for contributors:
```bash
./scripts/setup-dev.sh  # One-time setup
git checkout -b feature/your-feature
# Make changes, commit, push, create PR
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

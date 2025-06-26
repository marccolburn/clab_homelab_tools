# Installation Guide

## System Requirements

- Python 3.8 or higher
- macOS, Linux, or Windows
- Git (for cloning the repository)
- Root/admin access (for bridge management features)

## Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
# Test basic functionality
python main.py --help

# Run test suite
python -m pytest tests/ -v
```

## System-wide CLI Access (macOS)

To use the `clab-tools` command from anywhere on your system:

### Option 1: Automated Installation (Recommended)

```bash
# Run the installation script
./install-cli.sh

# Now you can use 'clab-tools' from anywhere
clab-tools --help
clab-tools import-csv -n nodes.csv -c connections.csv
```

### Option 2: Manual Symlink to /usr/local/bin

```bash
# Make the script executable (if not already done)
chmod +x clab-tools.sh

# Create a symlink in your PATH
sudo ln -sf "$(pwd)/clab-tools.sh" /usr/local/bin/clab-tools

# Now you can use 'clab-tools' from anywhere
clab-tools --help
clab-tools import-csv -n nodes.csv -c connections.csv
```

### Option 3: Add to PATH via shell profile

```bash
# Add the project directory to your PATH
echo 'export PATH="$PATH:'$(pwd)'"' >> ~/.zshrc
echo 'alias clab-tools="'$(pwd)'/clab-tools.sh"' >> ~/.zshrc

# Reload your shell configuration
source ~/.zshrc

# Now you can use 'clab-tools' from anywhere
clab-tools --help
```

**Note**: The script automatically resolves symlinks to find the correct Python virtual environment and project files, so it will work from any directory once installed system-wide. Even when called via the `/usr/local/bin/clab-tools` symlink, it correctly locates the original project directory.

## Dependencies

The project uses the following major dependencies:

### Core Dependencies
- **jinja2>=3.1.0** - Template engine for topology generation
- **click>=8.0.0** - CLI framework
- **pyyaml>=6.0** - YAML parsing for configuration
- **pandas>=2.0.0** - Data manipulation for CSV processing

### Enhanced Dependencies
- **sqlalchemy>=2.0.0** - ORM framework for database operations
- **alembic>=1.13.0** - Database migrations
- **pydantic>=2.0.0** - Data validation and settings
- **pydantic-settings>=2.0.0** - Settings management
- **structlog>=23.0.0** - Structured logging
- **rich>=13.0.0** - Rich terminal output

### Development & Testing
- **pytest>=7.0.0** - Testing framework
- **pytest-cov>=4.0.0** - Coverage testing
- **pytest-mock>=3.10.0** - Mock support for testing

## Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools

# Create development environment
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Verify development setup
python -m pytest tests/ --cov=clab_tools --cov-report=term-missing
```

## Docker Installation (Optional)

If you prefer containerized deployment:

```bash
# Create Dockerfile (example)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py", "--help"]
```

## Troubleshooting Installation

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version
python3 --version

# Use specific Python version if needed
python3.11 -m venv .venv
```

#### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Permission Issues (macOS/Linux)
```bash
# For bridge management features
sudo -v  # Verify sudo access

# For file permissions
chmod +x clab-tools.sh
```

#### Windows-Specific Issues
```powershell
# Use PowerShell for activation
.venv\Scripts\Activate.ps1

# If execution policy issues:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Create fresh environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Install one dependency at a time to identify conflicts
pip install jinja2
pip install click
# ... etc
```

### Testing Installation

```bash
# Basic functionality test
python main.py --version

# Import test with example data
python main.py import-csv -n example_nodes.csv -c example_connections.csv

# Show imported data
python main.py show-data

# Generate test topology
python main.py generate-topology -o test_lab.yml

# Clean up test data
python main.py clear-data --force
rm -f test_lab.yml clab_topology.db
```

## Next Steps

After successful installation:

1. Read the [User Guide](user-guide.md) for basic usage
2. Review [Configuration](configuration.md) for customization
3. Check [Troubleshooting](troubleshooting.md) for common issues

## Uninstallation

To completely remove the tool:

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf clab_homelab_tools
```

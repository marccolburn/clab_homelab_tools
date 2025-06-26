# Quick Reference - Containerlab Homelab Tools

## 🚀 One-Time Setup
```bash
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools
./scripts/setup-dev.sh  # For developers
# OR
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt  # For users
./install-cli.sh        # Install system-wide CLI
```

## 📋 Essential Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `clab-tools import-csv` | Import CSV data to database | `clab-tools import-csv -n nodes.csv -c connections.csv` |
| `clab-tools generate-topology` | Create topology YAML from database | `clab-tools generate-topology -o lab.yml -t "my_lab"` |
| `clab-tools show-data` | Display database contents | `clab-tools show-data` |
| `clab-tools create-bridges` | Create Linux bridges on host | `sudo clab-tools create-bridges --dry-run` |
| `clab-tools clear-data` | Clear database | `clab-tools clear-data --confirm` |

## 🔄 Typical Workflow

```bash
# 1. Import topology data
clab-tools import-csv -n nodes.csv -c connections.csv --clear-existing

# 2. Verify imported data
clab-tools show-data

# 3. Generate containerlab topology
clab-tools generate-topology -o my_lab.yml -t "production_lab" --validate

# 4. (Optional) Create host bridges
sudo clab-tools create-bridges --dry-run
sudo clab-tools create-bridges

# 5. Use with containerlab
containerlab deploy -t my_lab.yml
```

## 🗂️ File Locations

All output files are created in your **current working directory**:

```
your-project/
├── nodes.csv              # Input: Your network nodes
├── connections.csv         # Input: Your network connections
├── clab_topology.db       # Created: Database storage
└── my_lab.yml            # Output: Containerlab topology
```

## 🆘 Quick Help

```bash
clab-tools --help                    # Main help
clab-tools import-csv --help         # Command-specific help
clab-tools generate-topology --help  # Command-specific help
```

## 🔧 For Developers

```bash
./scripts/setup-dev.sh              # Complete dev setup
pytest tests/ -v --cov=clab_tools   # Run tests with coverage
pre-commit run --all-files          # Code quality checks
```

**Need more details?** See [Project Workflows & Architecture](docs/workflows-and-architecture.md) for comprehensive diagrams and workflows.

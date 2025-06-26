# Project Workflows and Architecture

This document provides clear visual workflows for different user types and explains the project structure to reduce confusion.

## 🎯 1. General Usage by End Users

### User Journey: From CSV to Containerlab Topology

```mermaid
graph TD
    A[User has CSV files] --> B[Clone Repository]
    B --> C[Setup Environment]
    C --> D[Install CLI Tool]
    D --> E[Import CSV Data]
    E --> F[Verify Data]
    F --> G[Generate Topology]
    G --> H[Use with Containerlab]

    C --> C1[python3 -m venv .venv<br/>source .venv/bin/activate<br/>pip install -r requirements.txt]
    D --> D1[./install-cli.sh<br/>Creates system-wide 'clab-tools' command]
    E --> E1[clab-tools import-csv -n nodes.csv -c connections.csv]
    F --> F1[clab-tools show-data]
    G --> G1[clab-tools generate-topology -o lab.yml]
    H --> H1[containerlab deploy -t lab.yml]

    style A fill:#e1f5fe
    style H fill:#c8e6c9
    style C1 fill:#fff3e0
    style D1 fill:#fff3e0
    style E1 fill:#fff3e0
    style F1 fill:#fff3e0
    style G1 fill:#fff3e0
    style H1 fill:#c8e6c9
```

### Simple User Commands Reference

| Step | Command | Purpose | Output Location |
|------|---------|---------|-----------------|
| 1 | `./install-cli.sh` | One-time CLI installation | System-wide `clab-tools` |
| 2 | `clab-tools import-csv -n nodes.csv -c connections.csv` | Import network data | Database in current directory |
| 3 | `clab-tools show-data` | Verify imported data | Console output |
| 4 | `clab-tools generate-topology -o lab.yml` | Create containerlab file | `lab.yml` in current directory |

### File Flow for Users

```
User Directory/
├── nodes.csv              # Input: Network nodes
├── connections.csv         # Input: Network connections
├── clab_topology.db       # Created: Database (SQLite)
└── lab.yml                # Output: Containerlab topology
```

**Key Points for Users:**
- ✅ All files created in your current working directory
- ✅ Database persists between sessions
- ✅ CLI works from any directory after installation
- ✅ No need to understand Python/development tools

---

## 🔧 2. Development and Testing by Contributors

### Developer Journey: From Code Change to Merge

```mermaid
graph TD
    A[Clone Repository] --> B[Setup Development Environment]
    B --> C[Create Feature Branch]
    C --> D[Make Code Changes]
    D --> E[Pre-commit Hooks Run]
    E --> F{Hooks Pass?}
    F -->|No| G[Fix Issues]
    G --> D
    F -->|Yes| H[Run Local Tests]
    H --> I{Tests Pass?}
    I -->|No| J[Fix Tests/Code]
    J --> D
    I -->|Yes| K[Push to GitHub]
    K --> L[Create Pull Request]
    L --> M[CI/CD Runs]
    M --> N{CI Passes?}
    N -->|No| O[Check CI Logs]
    O --> J
    N -->|Yes| P[Code Review]
    P --> Q[Merge to Main]

    B --> B1[./scripts/setup-dev.sh]
    C --> C1[git checkout -b feature/name]
    E --> E1[black, isort, flake8, yaml-check]
    H --> H1[pytest tests/ -v --cov=clab_tools]
    K --> K1[git push origin feature/name]
    M --> M1[Matrix: Ubuntu+macOS × Python 3.9-3.11]

    style A fill:#e1f5fe
    style Q fill:#c8e6c9
    style B1 fill:#fff3e0
    style C1 fill:#fff3e0
    style E1 fill:#fff3e0
    style H1 fill:#fff3e0
    style K1 fill:#fff3e0
    style M1 fill:#fff3e0
```

### Development Environment Setup

```
Repository Structure:
clab_homelab_tools/
├── 🔧 Development Tools
│   ├── scripts/setup-dev.sh          # One-command setup
│   ├── .pre-commit-config.yaml       # Code quality automation
│   ├── requirements-dev.txt          # Dev dependencies
│   └── .github/workflows/            # CI/CD pipelines
├── 📦 Application Code
│   ├── clab_tools/                   # Main Python package
│   ├── main.py                       # CLI entry point
│   ├── requirements.txt              # Runtime dependencies
│   └── config.yaml                   # Default configuration
├── 🧪 Testing
│   ├── tests/                        # Test suite
│   ├── pytest.ini                    # Test configuration
│   └── example_*.csv                 # Test data
├── 📚 Documentation
│   ├── docs/                         # Comprehensive docs
│   ├── README.md                     # Project overview
│   └── QUICK_REFERENCE.md            # Command summary
└── 🚀 Distribution
    ├── clab-tools.sh                 # CLI wrapper script
    └── install-cli.sh                # System installation
```

### Developer Commands Reference

| Stage | Command | Purpose | When to Use |
|-------|---------|---------|-------------|
| **Setup** | `./scripts/setup-dev.sh` | Complete dev environment | Once after clone |
| **Quality** | `pre-commit run --all-files` | Run all code checks | Before committing |
| **Testing** | `pytest tests/ -v --cov=clab_tools` | Full test with coverage | Before pushing |
| **Local CLI** | `./install-cli.sh` | Test CLI installation | Testing user experience |

### Code Quality Pipeline

```mermaid
graph LR
    A[Code Change] --> B[Pre-commit Hooks]
    B --> C[black: Format Code]
    C --> D[isort: Sort Imports]
    D --> E[flake8: Lint Code]
    E --> F[YAML: Validate Configs]
    F --> G[Tests: pytest]
    G --> H[Coverage: >85%]
    H --> I[Ready to Push]

    style A fill:#e1f5fe
    style I fill:#c8e6c9
```

---

## 🚀 3. GitHub CI/CD Workflow

### Automated Pipeline: From Push to Release

```mermaid
graph TD
    A[Developer Push/PR] --> B[GitHub Actions Triggered]
    B --> C[Matrix Build Start]
    C --> D[Ubuntu + Python 3.9]
    C --> E[Ubuntu + Python 3.10]
    C --> F[Ubuntu + Python 3.11]
    C --> G[macOS + Python 3.9]
    C --> H[macOS + Python 3.10]
    C --> I[macOS + Python 3.11]

    D --> J[Install Dependencies]
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J

    J --> K[Run Tests]
    K --> L[Integration Tests]
    L --> M{All Tests Pass?}
    M -->|No| N[❌ Block PR/Push]
    M -->|Yes| O[✅ Allow Merge]

    O --> P{Is Tag Push?}
    P -->|No| Q[Complete CI]
    P -->|Yes| R[Release Workflow]
    R --> S[Create GitHub Release]
    S --> T[Upload CLI Scripts]

    style A fill:#e1f5fe
    style N fill:#ffcdd2
    style O fill:#c8e6c9
    style T fill:#c8e6c9
```

### CI/CD Stages Breakdown

#### 1. **Continuous Integration (CI)**
- **Trigger**: Every push to `main`, every PR
- **Matrix**: 6 combinations (2 OS × 3 Python versions)
- **Tests**: Unit tests, integration tests, CLI tests
- **Artifacts**: Coverage reports (stored in GitHub)
- **Cost**: **FREE** (GitHub Actions free tier: 2000 minutes/month)

#### 2. **Quality Gates**
```
Required to Pass:
✅ All unit tests (pytest)
✅ Integration tests (CLI workflows)
✅ Code coverage maintains level
✅ No syntax errors
✅ All Python versions supported
```

#### 3. **Release Process**
- **Trigger**: Git tag push (e.g., `git tag v1.0.0 && git push origin v1.0.0`)
- **Actions**:
  - Run full CI pipeline
  - Create GitHub release
  - Upload CLI scripts as downloadable assets
- **Cost**: **FREE** (part of GitHub's free features)

### GitHub Features Used (All Free)

| Feature | Purpose | Cost | Notes |
|---------|---------|------|-------|
| **GitHub Actions** | CI/CD automation | FREE | 2000 minutes/month free |
| **Artifact Storage** | Coverage reports | FREE | 500MB free storage |
| **Releases** | Tagged releases | FREE | Unlimited |
| **Issue Tracking** | Bug reports, features | FREE | Unlimited |
| **Pull Requests** | Code review | FREE | Unlimited |
| **Branch Protection** | Enforce quality | FREE | Core feature |

**💰 Cost Guarantee**: This setup uses ZERO paid GitHub features!

---

## 📊 Project Structure Overview

### Logical Component Separation

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Commands<br/>main.py]
        SCRIPT[System Script<br/>clab-tools.sh]
    end

    subgraph "Business Logic Layer"
        CSV[CSV Import<br/>clab_tools/commands/]
        TOPO[Topology Generation<br/>clab_tools/topology/]
        BRIDGE[Bridge Management<br/>clab_tools/bridges/]
    end

    subgraph "Data Layer"
        DB[Database ORM<br/>clab_tools/db/]
        CONFIG[Configuration<br/>clab_tools/config/]
    end

    subgraph "Infrastructure Layer"
        LOG[Logging<br/>clab_tools/logging/]
        ERROR[Error Handling<br/>clab_tools/errors/]
    end

    CLI --> CSV
    CLI --> TOPO
    CLI --> BRIDGE
    SCRIPT --> CLI

    CSV --> DB
    TOPO --> DB
    BRIDGE --> DB

    CSV --> CONFIG
    TOPO --> CONFIG
    BRIDGE --> CONFIG

    CSV --> LOG
    TOPO --> LOG
    BRIDGE --> LOG
    DB --> LOG

    CSV --> ERROR
    TOPO --> ERROR
    BRIDGE --> ERROR
    DB --> ERROR

    style CLI fill:#e3f2fd
    style SCRIPT fill:#e3f2fd
    style CSV fill:#f3e5f5
    style TOPO fill:#f3e5f5
    style BRIDGE fill:#f3e5f5
    style DB fill:#e8f5e8
    style CONFIG fill:#e8f5e8
    style LOG fill:#fff3e0
    style ERROR fill:#fff3e0
```

### File Organization Logic

```
📁 Top Level (Minimal)
├── README.md              # 📋 Project overview only
├── QUICK_REFERENCE.md     # 🚀 Command cheat sheet
├── main.py               # 🎯 CLI entry point
├── requirements.txt      # 📦 Dependencies
├── clab-tools.sh        # 🔧 System CLI wrapper
└── install-cli.sh       # ⚙️ Installation script

📁 docs/ (Detailed Documentation)
├── installation.md       # 📖 Setup instructions
├── user-guide.md         # 👤 End user workflows
├── development-workflow.md # 🔧 Developer processes
├── configuration.md      # ⚙️ Settings and options
├── architecture.md       # 🏗️ Technical design
├── troubleshooting.md    # 🐛 Problem solving
└── api-reference.md      # 📚 Complete CLI reference

📁 Application Code
├── clab_tools/           # 🐍 Python package
├── tests/               # 🧪 Test suite
└── scripts/             # 🔧 Development utilities

📁 GitHub Integration
└── .github/             # 🚀 CI/CD and templates
```

## 🎯 Quick Navigation Guide

**I want to...**

| Goal | Go to | Quick Command |
|------|-------|---------------|
| **Use the tool** | [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) | `clab-tools --help` |
| **Install it** | [docs/installation.md](installation.md) | `./install-cli.sh` |
| **Contribute code** | [docs/development-workflow.md](development-workflow.md) | `./scripts/setup-dev.sh` |
| **Understand architecture** | [docs/architecture.md](architecture.md) | Read diagrams above |
| **Fix problems** | [docs/troubleshooting.md](troubleshooting.md) | Check logs |
| **Configure it** | [docs/configuration.md](configuration.md) | Edit `config.yaml` |

**This document eliminates confusion by showing exactly who does what, when, and how!** 🎉

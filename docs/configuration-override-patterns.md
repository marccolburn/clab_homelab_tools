# Configuration Override Patterns and Best Practices

This guide provides practical patterns and best practices for overriding configuration in the Containerlab Homelab Tools, with a focus on local development and team workflows.

## Quick Reference: Override Priority

Configuration is applied in this order (later overrides earlier):

1. **Built-in defaults** (lowest priority)
2. **Main config file** (`config.yaml`)
3. **Local config file** (e.g., `config.local.yaml`)
4. **Environment variables** (`CLAB_*`)
5. **Command-line options** (highest priority)

## Local Configuration Patterns

### Pattern 1: Local Override File

The most common pattern for local development is using a separate local config file:

**Project Structure:**
```
your-project/
├── config.yaml                 # Committed to git (team defaults)
├── config.local.yaml          # Local overrides (ignored by git)
├── config.dev.yaml            # Development environment
├── config.test.yaml           # Testing environment
└── config.prod.yaml           # Production environment
```

**Main config.yaml (committed):**
```yaml
# Team defaults - safe to commit
database:
  url: "sqlite:///clab_topology.db"
  echo: false

logging:
  level: "INFO"
  format: "console"

topology:
  default_prefix: "clab"
  default_mgmt_network: "clab"
  default_mgmt_subnet: "172.20.20.0/24"

debug: false
```

**config.local.yaml (not committed):**
```yaml
# Local development overrides
# Add this file to .gitignore
database:
  url: "sqlite:///my_dev.db"
  echo: true

logging:
  level: "DEBUG"

# Override just what you need for local development
topology:
  default_prefix: "mydev"

debug: true
```

**Usage:**
```bash
# Use local config
clab-tools --config config.local.yaml import-csv nodes.csv

# Still works with original config
clab-tools import-csv nodes.csv
```

### Pattern 2: Environment-Specific Configs

Create dedicated config files for different environments:

**config.dev.yaml:**
```yaml
database:
  url: "sqlite:///dev_clab.db"
  echo: true

logging:
  level: "DEBUG"
  format: "console"

topology:
  default_prefix: "dev"
  default_mgmt_subnet: "172.30.0.0/24"

debug: true
```

**config.staging.yaml:**
```yaml
database:
  url: "postgresql://clab_user:${DB_PASSWORD}@staging-db:5432/clab_staging"
  pool_size: 5

logging:
  level: "INFO"
  format: "json"
  file_path: "/tmp/clab-staging.log"

topology:
  default_prefix: "staging"
  default_mgmt_subnet: "10.staging.0.0/16"

debug: false
```

**config.prod.yaml:**
```yaml
database:
  url: "postgresql://clab_user:${DB_PASSWORD}@prod-db:5432/clab_production"
  pool_size: 10
  max_overflow: 20

logging:
  level: "WARNING"
  format: "json"
  file_path: "/var/log/clab/production.log"
  max_file_size: 104857600  # 100MB
  backup_count: 10

topology:
  default_prefix: "production"
  default_mgmt_subnet: "10.prod.0.0/16"

bridges:
  bridge_prefix: "prod-br"
  cleanup_on_exit: false

debug: false
```

### Pattern 3: User-Specific Overrides

For teams where each developer has different preferences:

**config.yaml (team defaults):**
```yaml
database:
  url: "sqlite:///clab_topology.db"

logging:
  level: "INFO"
  format: "console"

topology:
  default_prefix: "clab"
```

**config.alice.yaml (Alice's preferences):**
```yaml
database:
  url: "sqlite:///alice_clab.db"
  echo: true

logging:
  level: "DEBUG"
  format: "json"

topology:
  default_prefix: "alice"
  default_mgmt_subnet: "172.25.0.0/24"

debug: true
```

**config.bob.yaml (Bob's preferences):**
```yaml
database:
  url: "postgresql://bob:${BOB_DB_PASSWORD}@localhost/bob_clab"

logging:
  level: "INFO"
  format: "console"
  file_path: "/Users/bob/logs/clab.log"

topology:
  default_prefix: "bob"
  default_mgmt_subnet: "10.200.0.0/16"

debug: false
```

## Environment Variable Patterns

### Pattern 1: Development Environment Variables

Create a `.env.local` file (add to .gitignore):

```bash
# .env.local - Local development overrides
export CLAB_DEBUG="true"
export CLAB_LOGGING_LEVEL="DEBUG"
export CLAB_LOGGING_FORMAT="console"
export CLAB_DATABASE_URL="sqlite:///my_dev.db"
export CLAB_DATABASE_ECHO="true"
export CLAB_TOPOLOGY_DEFAULT_PREFIX="mydev"
```

**Usage:**
```bash
# Load local environment
source .env.local

# Now run commands with overrides
clab-tools import-csv nodes.csv
```

### Pattern 2: Per-Project Environment

For different projects using the same tool:

```bash
# project-a/.env
export CLAB_DATABASE_URL="sqlite:///project_a.db"
export CLAB_TOPOLOGY_DEFAULT_PREFIX="proj-a"
export CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET="172.20.0.0/24"

# project-b/.env
export CLAB_DATABASE_URL="sqlite:///project_b.db"
export CLAB_TOPOLOGY_DEFAULT_PREFIX="proj-b"
export CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET="172.21.0.0/24"
```

### Pattern 3: CI/CD Environment Variables

Set in your CI/CD pipeline:

```yaml
# GitHub Actions example
env:
  CLAB_DATABASE_URL: "sqlite:///:memory:"
  CLAB_LOGGING_LEVEL: "WARNING"
  CLAB_LOGGING_FORMAT: "json"
  CLAB_DEBUG: "false"
```

## Command-Line Override Patterns

### Pattern 1: Quick Testing

```bash
# Quick database switch for testing
clab-tools --db-url "sqlite:///test.db" show-data

# Test with debug mode
clab-tools --debug --log-level DEBUG import-csv nodes.csv

# Use different config for one command
clab-tools --config config.test.yaml generate-topology
```

### Pattern 2: Scripted Overrides

```bash
#!/bin/bash
# deploy.sh - Deployment script with overrides

ENVIRONMENT=${1:-staging}

case $ENVIRONMENT in
  "staging")
    CONFIG_FILE="config.staging.yaml"
    LOG_LEVEL="INFO"
    ;;
  "production")
    CONFIG_FILE="config.prod.yaml"
    LOG_LEVEL="WARNING"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

clab-tools \
  --config "$CONFIG_FILE" \
  --log-level "$LOG_LEVEL" \
  --log-format "json" \
  generate-topology
```

### Pattern 3: Complex Override Combinations

```bash
# Start with staging config, but override specific settings
clab-tools \
  --config config.staging.yaml \
  --db-url "postgresql://user:pass@local-db:5432/debug_db" \
  --log-level DEBUG \
  --debug \
  import-csv nodes.csv
```

## Git Integration Best Practices

### .gitignore Patterns

Add these patterns to your `.gitignore`:

```gitignore
# Local configuration overrides
config.local.yaml
config.*.local.yaml
*.local.yaml

# Environment files with secrets
.env.local
.env.*.local

# User-specific configs (if using name pattern)
config.*.yaml
!config.example.yaml
!config.template.yaml

# Database files (if using SQLite locally)
*.db
*.sqlite
*.sqlite3

# Local log files
logs/
*.log
```

### Example Configuration

**config.example.yaml (committed as template):**
```yaml
# Example configuration - copy to config.local.yaml and customize
database:
  url: "sqlite:///your_database.db"  # Change this
  echo: false

logging:
  level: "INFO"                      # Change to DEBUG for development
  format: "console"

topology:
  default_prefix: "yourname"         # Change this
  default_mgmt_subnet: "172.20.20.0/24"

debug: false                         # Change to true for development
```

**README.md section:**
```markdown
## Local Development Setup

1. Copy the example configuration:
   ```bash
   cp config.example.yaml config.local.yaml
   ```

2. Edit `config.local.yaml` with your preferences:
   - Change `database.url` to your local database
   - Change `topology.default_prefix` to your name/project
   - Set `debug: true` for development
   - Set `logging.level: "DEBUG"` for verbose output

3. Use your local config:
   ```bash
   clab-tools --config config.local.yaml import-csv nodes.csv
   ```
```

## Team Workflow Patterns

### Pattern 1: Shared Defaults + Local Overrides

```yaml
# config.yaml (committed) - team defaults
database:
  url: "sqlite:///clab_topology.db"
logging:
  level: "INFO"
  format: "console"
topology:
  default_prefix: "clab"
  default_mgmt_network: "clab"
```

Each developer creates their own `config.local.yaml` with personal preferences.

### Pattern 2: Multiple Named Environments

```bash
# Team uses consistent environment names
clab-tools --config config.dev.yaml      # Development
clab-tools --config config.staging.yaml  # Staging
clab-tools --config config.prod.yaml     # Production
```

### Pattern 3: Environment Variable Standards

Define team standards for environment variables:

```bash
# Standard development environment
export CLAB_ENV="development"
export CLAB_DEBUG="true"
export CLAB_LOGGING_LEVEL="DEBUG"

# Standard testing environment
export CLAB_ENV="testing"
export CLAB_DATABASE_URL="sqlite:///:memory:"
export CLAB_LOGGING_LEVEL="WARNING"
```

## Advanced Override Patterns

### Pattern 1: Conditional Configuration

Use environment variables in YAML files:

```yaml
# config.yaml
database:
  url: "${DATABASE_URL:-sqlite:///clab_topology.db}"

logging:
  level: "${LOG_LEVEL:-INFO}"
  format: "${LOG_FORMAT:-console}"
  file_path: "${LOG_FILE_PATH}"

topology:
  default_prefix: "${CLAB_PREFIX:-clab}"

debug: ${DEBUG:-false}
```

### Pattern 2: Profile-Based Configuration

```bash
#!/bin/bash
# profiles.sh - Profile-based configuration

load_profile() {
  local profile=$1

  case $profile in
    "minimal")
      export CLAB_LOGGING_LEVEL="WARNING"
      export CLAB_DATABASE_URL="sqlite:///:memory:"
      ;;
    "developer")
      export CLAB_DEBUG="true"
      export CLAB_LOGGING_LEVEL="DEBUG"
      export CLAB_DATABASE_ECHO="true"
      ;;
    "testing")
      export CLAB_DATABASE_URL="sqlite:///:memory:"
      export CLAB_LOGGING_FORMAT="json"
      ;;
  esac
}

# Usage: source profiles.sh && load_profile developer
```

### Pattern 3: Dynamic Configuration

```python
#!/usr/bin/env python3
# dynamic_config.py - Generate config based on environment

import os
import yaml

def generate_config():
    """Generate configuration based on current environment."""

    # Detect environment
    if os.path.exists("/tmp/is_docker"):
        env = "docker"
    elif os.getenv("CI"):
        env = "ci"
    elif os.getenv("USER") == "developer":
        env = "development"
    else:
        env = "default"

    configs = {
        "docker": {
            "database": {"url": "sqlite:///docker_clab.db"},
            "logging": {"level": "INFO", "format": "json"},
        },
        "ci": {
            "database": {"url": "sqlite:///:memory:"},
            "logging": {"level": "WARNING", "format": "json"},
        },
        "development": {
            "database": {"url": "sqlite:///dev_clab.db", "echo": True},
            "logging": {"level": "DEBUG", "format": "console"},
            "debug": True,
        },
        "default": {
            "database": {"url": "sqlite:///clab_topology.db"},
            "logging": {"level": "INFO", "format": "console"},
        }
    }

    with open(f"config.{env}.yaml", "w") as f:
        yaml.dump(configs[env], f, default_flow_style=False)

    return f"config.{env}.yaml"

if __name__ == "__main__":
    config_file = generate_config()
    print(f"Generated: {config_file}")
```

## Troubleshooting Configuration Overrides

### Debug Configuration Loading

```bash
# See what configuration is actually loaded
clab-tools --debug show-data 2>&1 | grep -i config

# Test specific config file
clab-tools --config config.local.yaml --debug show-data
```

### Validate Override Behavior

```python
#!/usr/bin/env python3
# validate_config.py - Test configuration override behavior

import sys
import os
sys.path.insert(0, '.')

from clab_tools.config.settings import initialize_settings

def test_config_override():
    """Test configuration override behavior."""

    print("=== Testing Configuration Override ===")

    # Test 1: Default configuration
    print("\n1. Default configuration:")
    settings = initialize_settings()
    print(f"   Database URL: {settings.database.url}")
    print(f"   Log Level: {settings.logging.level}")
    print(f"   Debug: {settings.debug}")

    # Test 2: Config file override
    if os.path.exists("config.local.yaml"):
        print("\n2. With config.local.yaml:")
        settings = initialize_settings(config_file="config.local.yaml")
        print(f"   Database URL: {settings.database.url}")
        print(f"   Log Level: {settings.logging.level}")
        print(f"   Debug: {settings.debug}")

    # Test 3: Environment variable override
    print("\n3. With environment variables:")
    os.environ["CLAB_DATABASE_URL"] = "sqlite:///env_test.db"
    os.environ["CLAB_DEBUG"] = "true"
    settings = initialize_settings()
    print(f"   Database URL: {settings.database.url}")
    print(f"   Debug: {settings.debug}")

    # Clean up
    del os.environ["CLAB_DATABASE_URL"]
    del os.environ["CLAB_DEBUG"]

if __name__ == "__main__":
    test_config_override()
```

### Common Override Issues

#### Issue: Config file not found
```bash
# Problem: File path is relative
clab-tools --config config.local.yaml

# Solution: Use absolute path
clab-tools --config /full/path/to/config.local.yaml

# Or ensure you're in the right directory
cd /path/to/project
clab-tools --config config.local.yaml
```

#### Issue: Environment variables not working
```bash
# Problem: Wrong variable name
export CLAB_DATABASE="sqlite:///test.db"  # Wrong

# Solution: Use correct variable name
export CLAB_DATABASE_URL="sqlite:///test.db"  # Correct

# Verify variable is set
echo $CLAB_DATABASE_URL
```

#### Issue: Overrides not taking effect
```bash
# Check override priority
# Command line > Environment > Config file > Defaults

# This WILL override config file:
clab-tools --config config.yaml --db-url "sqlite:///override.db"

# This will NOT override command line:
CLAB_DATABASE_URL="sqlite:///env.db" clab-tools --db-url "sqlite:///cli.db"
```

## Summary

The Containerlab Homelab Tools provides a flexible configuration system that supports:

1. **Local config files** for personal development preferences
2. **Environment variables** for deployment and CI/CD
3. **Command-line options** for one-off overrides
4. **Multiple config files** for different environments

Choose the pattern that best fits your workflow:
- **Individual developers**: Use `config.local.yaml`
- **Team environments**: Use named configs like `config.dev.yaml`
- **CI/CD**: Use environment variables
- **Quick testing**: Use command-line options

For more information, see:
- [Configuration Guide](configuration.md) - Complete configuration reference
- [User Guide](user-guide.md) - General usage patterns
- [Developer Guide](developer-guide.md) - Development workflow

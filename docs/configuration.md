# Configuration Guide

Comprehensive guide to configuring the Containerlab Homelab Tools.

## Configuration Hierarchy

Settings are loaded in this order (later sources override earlier ones):

1. **Default values** (built into the application)
2. **Configuration file** (YAML)
3. **Environment variables** (CLAB_* prefix)
4. **Command-line options** (highest priority)

## Configuration File

### Basic Configuration

Create a `config.yaml` file in your project directory:

```yaml
# Basic configuration
database:
  url: "sqlite:///clab_topology.db"

logging:
  level: "INFO"
  format: "console"

topology:
  default_prefix: "clab"
  default_mgmt_network: "clab"
  default_mgmt_subnet: "172.20.20.0/24"
```

### Complete Configuration

```yaml
# Complete configuration with all options
database:
  url: "sqlite:///clab_topology.db"
  echo: false                    # Set to true for SQL debugging
  pool_pre_ping: true           # Enable connection health checks
  pool_timeout: 30              # Connection timeout in seconds
  pool_recycle: 3600           # Recycle connections every hour

logging:
  level: "INFO"                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "console"             # console or json
  file_path: null               # Optional: "logs/clab.log"
  max_file_size: 10485760      # 10MB
  backup_count: 5              # Keep 5 old log files
  structured: true             # Enable structured logging

topology:
  default_prefix: "clab"
  default_mgmt_network: "clab"
  default_mgmt_subnet: "172.20.20.0/24"
  template_path: "topology_template.j2"
  output_dir: "."
  validate_output: true
  kinds_config_path: "supported_kinds.yaml"

bridges:
  bridge_prefix: "clab-br"
  cleanup_on_exit: false
  verify_creation: true
  timeout: 30

# General settings
debug: false
```

### Environment-Specific Configurations

#### Development Configuration
```yaml
# dev-config.yaml
database:
  url: "sqlite:///dev_clab.db"
  echo: true                    # Enable SQL debugging

logging:
  level: "DEBUG"
  format: "console"

debug: true
```

#### Production Configuration
```yaml
# prod-config.yaml
database:
  url: "postgresql://clab:password@db-server/clab_prod"
  pool_size: 10
  max_overflow: 20

logging:
  level: "INFO"
  format: "json"
  file_path: "/var/log/clab/clab.log"

debug: false
```

#### Testing Configuration
```yaml
# test-config.yaml
database:
  url: "sqlite:///:memory:"     # In-memory database for tests

logging:
  level: "WARNING"
  format: "json"

debug: false
```

## Environment Variables

All configuration options can be set via environment variables using the `CLAB_` prefix.

### Variable Naming Convention

Configuration path → Environment variable:
- `database.url` → `CLAB_DATABASE_URL`
- `logging.level` → `CLAB_LOGGING_LEVEL`
- `topology.default_prefix` → `CLAB_TOPOLOGY_DEFAULT_PREFIX`

### Common Environment Variables

```bash
# Database configuration
export CLAB_DATABASE_URL="postgresql://user:pass@host/db"
export CLAB_DATABASE_ECHO="true"

# Logging configuration
export CLAB_LOGGING_LEVEL="DEBUG"
export CLAB_LOGGING_FORMAT="json"
export CLAB_LOGGING_FILE_PATH="/var/log/clab.log"

# Topology configuration
export CLAB_TOPOLOGY_DEFAULT_PREFIX="production"
export CLAB_TOPOLOGY_DEFAULT_MGMT_SUBNET="192.168.100.0/24"

# Bridge configuration
export CLAB_BRIDGES_BRIDGE_PREFIX="prod-br"
export CLAB_BRIDGES_CLEANUP_ON_EXIT="true"

# General settings
export CLAB_DEBUG="true"
```

### Environment Examples

#### Development Environment
```bash
#!/bin/bash
# dev-env.sh
export CLAB_DEBUG="true"
export CLAB_LOGGING_LEVEL="DEBUG"
export CLAB_LOGGING_FORMAT="console"
export CLAB_DATABASE_URL="sqlite:///dev.db"
export CLAB_DATABASE_ECHO="true"
```

#### Production Environment
```bash
#!/bin/bash
# prod-env.sh
export CLAB_DEBUG="false"
export CLAB_LOGGING_LEVEL="INFO"
export CLAB_LOGGING_FORMAT="json"
export CLAB_LOGGING_FILE_PATH="/var/log/clab/clab.log"
export CLAB_DATABASE_URL="postgresql://clab:${DB_PASSWORD}@${DB_HOST}/clab_prod"
```

#### CI/CD Environment
```bash
#!/bin/bash
# ci-env.sh
export CLAB_LOGGING_FORMAT="json"
export CLAB_LOGGING_LEVEL="WARNING"
export CLAB_DATABASE_URL="sqlite:///:memory:"
export CLAB_DEBUG="false"
```

## Command-Line Options

Override any configuration option directly from the command line:

```bash
# Override configuration file
python main.py --config production.yaml show-data

# Override database URL
python main.py --db-url "postgresql://user:pass@host/db" show-data

# Override logging settings
python main.py --log-level DEBUG --log-format json show-data

# Enable debug mode
python main.py --debug show-data

# Combine multiple overrides
python main.py --config prod.yaml --debug --log-level DEBUG show-data
```

## Database Configuration

### SQLite (Default)

```yaml
database:
  url: "sqlite:///clab_topology.db"
  # SQLite-specific options
  timeout: 20
  isolation_level: null
```

### PostgreSQL

```yaml
database:
  url: "postgresql://username:password@host:port/database"
  # PostgreSQL-specific options
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
  pool_pre_ping: true
```

### MySQL

```yaml
database:
  url: "mysql+pymysql://username:password@host:port/database"
  # MySQL-specific options
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
```

### Connection Pooling

```yaml
database:
  url: "postgresql://user:pass@host/db"
  pool_size: 5              # Number of connections to maintain
  max_overflow: 10          # Additional connections allowed
  pool_timeout: 30          # Timeout for getting connection
  pool_recycle: 3600        # Recycle connections after 1 hour
  pool_pre_ping: true       # Verify connections before use
```

## Logging Configuration

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Warning messages for unexpected situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause termination

### Log Formats

#### Console Format (Default)
Human-readable colored output for terminal use:
```yaml
logging:
  format: "console"
```

#### JSON Format
Structured JSON for log aggregation systems:
```yaml
logging:
  format: "json"
```

### File Logging

```yaml
logging:
  file_path: "/var/log/clab/clab.log"
  max_file_size: 10485760    # 10MB
  backup_count: 5            # Keep 5 old files
```

### Advanced Logging

```yaml
logging:
  level: "INFO"
  format: "console"
  file_path: "logs/clab.log"
  max_file_size: 52428800    # 50MB
  backup_count: 10
  structured: true           # Enable structured logging
  include_caller: true       # Include function/line info
  enable_colors: true        # Enable colored output
```

## Topology Configuration

### Default Settings

```yaml
topology:
  default_prefix: "clab"                    # Containerlab prefix
  default_mgmt_network: "clab"             # Management network name
  default_mgmt_subnet: "172.20.20.0/24"   # Management subnet
  template_path: "topology_template.j2"    # Jinja2 template file
  output_dir: "."                          # Output directory
  validate_output: true                    # Validate generated YAML
  kinds_config_path: "supported_kinds.yaml"
```

### Custom Template

```yaml
topology:
  template_path: "custom_templates/my_template.j2"
  # Template variables can be added here
  custom_variables:
    company_name: "My Company"
    environment: "production"
```

### Multiple Templates

```yaml
topology:
  templates:
    default: "topology_template.j2"
    minimal: "minimal_template.j2"
    advanced: "advanced_template.j2"
```

## Bridge Configuration

### Basic Settings

```yaml
bridges:
  bridge_prefix: "clab-br"     # Prefix for bridge names
  cleanup_on_exit: false      # Auto-cleanup on exit
  verify_creation: true       # Verify bridges are created
  timeout: 30                 # Timeout for operations
```

### Advanced Settings

```yaml
bridges:
  bridge_prefix: "prod-br"
  cleanup_on_exit: true
  verify_creation: true
  timeout: 60
  # Custom bridge configuration
  mtu: 1500
  stp: false                  # Disable spanning tree
  ageing_time: 300           # MAC address ageing time
```

## Security Considerations

### Sensitive Data

Never include sensitive data in configuration files committed to version control:

```yaml
# ❌ DON'T DO THIS
database:
  url: "postgresql://user:secret_password@host/db"
```

Instead, use environment variables:

```yaml
# ✅ DO THIS
database:
  url: "${DATABASE_URL}"  # Set via environment variable
```

### Configuration File Permissions

```bash
# Secure configuration file permissions
chmod 600 config.yaml
chown user:user config.yaml
```

### Environment Variable Security

```bash
# Use a secure environment file
cat > .env << EOF
CLAB_DATABASE_URL="postgresql://user:${DB_PASSWORD}@host/db"
EOF

chmod 600 .env

# Load environment
source .env
```

## Validation

The configuration system automatically validates all settings. Invalid configurations will produce helpful error messages:

```bash
# Example validation error
✗ Error: Log level must be one of: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
```

### Custom Validation

You can validate your configuration without running commands:

```bash
# Validate configuration file
python -c "
from clab_tools.config import get_settings
try:
    settings = get_settings('config.yaml')
    print('✓ Configuration is valid')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"
```

## Configuration Examples

### Minimal Configuration

```yaml
# minimal-config.yaml
database:
  url: "sqlite:///simple.db"
logging:
  level: "INFO"
```

### Development Configuration

```yaml
# dev-config.yaml
database:
  url: "sqlite:///dev.db"
  echo: true

logging:
  level: "DEBUG"
  format: "console"

topology:
  default_prefix: "dev"

debug: true
```

### Production Configuration

```yaml
# prod-config.yaml
database:
  url: "postgresql://clab:${DB_PASSWORD}@${DB_HOST}/clab_prod"
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30

logging:
  level: "INFO"
  format: "json"
  file_path: "/var/log/clab/clab.log"
  max_file_size: 52428800
  backup_count: 10

topology:
  default_prefix: "production"
  default_mgmt_subnet: "10.100.0.0/16"

bridges:
  bridge_prefix: "prod-br"
  cleanup_on_exit: false

debug: false
```

### High-Availability Configuration

```yaml
# ha-config.yaml
database:
  url: "postgresql://clab:${DB_PASSWORD}@${DB_HOST}/clab_ha"
  pool_size: 20
  max_overflow: 40
  pool_timeout: 10
  pool_recycle: 1800
  pool_pre_ping: true

logging:
  level: "INFO"
  format: "json"
  file_path: "/var/log/clab/clab.log"
  max_file_size: 104857600  # 100MB
  backup_count: 20

topology:
  default_prefix: "ha"
  validate_output: true

bridges:
  verify_creation: true
  timeout: 120

debug: false
```

## Troubleshooting Configuration

### Common Issues

#### Configuration File Not Found
```bash
# Specify absolute path
python main.py --config /absolute/path/to/config.yaml show-data

# Check current directory
ls -la config.yaml
```

#### Environment Variable Not Recognized
```bash
# Check variable name format
echo $CLAB_DATABASE_URL

# List all CLAB_ variables
env | grep CLAB_
```

#### Database Connection Issues
```bash
# Test database connectivity
python main.py --debug --db-url "your-database-url" show-data
```

#### Permission Issues
```bash
# Check file permissions
ls -la config.yaml

# Fix permissions
chmod 644 config.yaml
```

### Debug Configuration

```bash
# Show current configuration
python -c "
from clab_tools.config import get_settings
import json
settings = get_settings()
print(json.dumps(settings.model_dump(), indent=2))
"

# Test specific configuration
python main.py --config test-config.yaml --debug show-data
```

For more information, see:
- [User Guide](user-guide.md)
- [Developer Guide](developer-guide.md)
- [Troubleshooting](troubleshooting.md)

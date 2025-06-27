# Troubleshooting Guide

Common issues and solutions for clab-tools.

## Quick Diagnosis

```bash
# Check installation
./clab-tools.sh --version
./clab-tools.sh --help

# Test database
./clab-tools.sh data show

# Test configuration
./clab-tools.sh remote show-config

# Enable debug mode
./clab-tools.sh --debug --verbose [command]
```

## Installation Issues

### Command Not Found

**Problem**: `./clab-tools.sh: command not found`

**Solutions**:
```bash
# Make executable
chmod +x clab-tools.sh

# Check Python installation
python3 --version

# Reinstall dependencies
pip install -r requirements.txt
```

### Python Module Errors

**Problem**: `ModuleNotFoundError: No module named 'click'`

**Solutions**:
```bash
# Install in virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Or install globally
pip3 install -r requirements.txt
```

## Database Issues

### Database Connection Errors

**Problem**: `Database file not found` or connection errors

**Solutions**:
```bash
# Initialize database
./clab-tools.sh db init

# Check database location
ls -la clab_topology.db

# Reset database
rm clab_topology.db
./clab-tools.sh db init
```

### Data Import Issues

**Problem**: CSV import fails or data corruption

**Solutions**:
```bash
# Validate CSV format first
head -1 nodes.csv

# Clear and re-import
./clab-tools.sh data clear
./clab-tools.sh data import -n nodes.csv -c connections.csv
```

## Bridge and Network Issues

### Bridge Creation Failures

**Problem**: Bridge creation fails with permission errors

**Solutions**:
```bash
# Run with sudo
sudo ./clab-tools.sh bridge create br-mgmt

# Check existing bridges
ip link show type bridge

# Cleanup failed bridges
sudo ip link delete br-mgmt type bridge
```

### Network Interface Issues

**Problem**: Interface not found or in use

**Solutions**:
```bash
# List available interfaces
ip link show

# Check interface status
ip link show eth0

# Bring interface down if needed
sudo ip link set eth0 down
```

## Remote Host Issues

### SSH Connection Problems

**Problem**: Cannot connect to remote hosts

**Solutions**:
```bash
# Test SSH manually
ssh -v user@remote-host

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Update known_hosts
ssh-keyscan -H remote-host >> ~/.ssh/known_hosts
```

### Remote Command Failures

**Problem**: Commands fail on remote hosts

**Solutions**:
```bash
# Test remote connectivity
./clab-tools.sh remote test-connection hostname

# Check remote containerlab installation
ssh user@remote-host "which containerlab"

# Check remote sudo access
ssh user@remote-host "sudo -l"
```

## Containerlab Integration

### Containerlab Not Found

**Problem**: `containerlab: command not found`

**Solutions**:
```bash
# Install containerlab
bash -c "$(curl -sL https://get.containerlab.dev)"

# Or use package manager
sudo apt install containerlab  # Ubuntu/Debian
brew install containerlab      # macOS
```

### Docker/Container Issues

**Problem**: Container runtime errors

**Solutions**:
```bash
# Check Docker status
docker --version
systemctl status docker

# Test container access
docker run --rm hello-world

# Check containerlab version
containerlab version
```

## Configuration Issues

### Config File Errors

**Problem**: YAML parsing errors or invalid configuration

**Solutions**:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Show effective configuration
./clab-tools.sh config show

# Reset to defaults
cp config.local.example.yaml config.local.yaml
```

### Environment Variable Issues

**Problem**: Environment variables not recognized

**Solutions**:
```bash
# Check current environment
env | grep CLAB

# Set environment variables
export CLAB_PROJECT_NAME="my-lab"
export CLAB_LOG_LEVEL="DEBUG"

# Make permanent in shell profile
echo 'export CLAB_PROJECT_NAME="my-lab"' >> ~/.bashrc
```

## Performance Issues

### Slow Database Operations

**Problem**: Database queries taking too long

**Solutions**:
```bash
# Rebuild database with indexes
./clab-tools.sh db init --rebuild

# Check database size
ls -lh clab_topology.db

# Optimize database
sqlite3 clab_topology.db "VACUUM;"
```

### Large Topology Generation

**Problem**: Topology generation times out or fails

**Solutions**:
```bash
# Generate in smaller batches
./clab-tools.sh topology generate --max-nodes 50

# Increase timeout
export CLAB_TIMEOUT=300
./clab-tools.sh topology generate

# Use streaming mode for large datasets
./clab-tools.sh topology generate --stream
```

## Debug Mode

### Enable Verbose Logging

```bash
# Full debug output
./clab-tools.sh --debug --verbose command

# Log to file
./clab-tools.sh --debug command 2>&1 | tee debug.log

# Set environment variable
export CLAB_LOG_LEVEL=DEBUG
```

### Common Debug Commands

```bash
# Show all data
./clab-tools.sh data show

# Test remote connection
./clab-tools.sh remote test-connection

# Show remote configuration
./clab-tools.sh remote show-config
```

## Getting Help

### Log Information

When reporting issues, include:

```bash
# System information
./clab-tools.sh --version
python3 --version
uname -a

# Configuration
./clab-tools.sh config show

# Error output with debug
./clab-tools.sh --debug [failing-command] 2>&1
```

### Common Support Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check [User Guide](user-guide.md) and [Commands](commands.md)
- **Examples**: Review CSV format in [CSV Format Guide](csv-format.md)
- **Development**: See [Development Guide](development.md) for contributing

### Reset Everything

If all else fails, complete reset:

```bash
# Backup current data
cp clab_topology.db clab_topology.db.backup
cp config.yaml config.yaml.backup

# Clean slate
rm clab_topology.db config.local.yaml
./clab-tools.sh db init
cp config.local.example.yaml config.local.yaml

# Reimport data
./clab-tools.sh data import -n nodes.csv -c connections.csv
```
```

**Solution**:
```bash
# Verify virtual environment is activated
echo $VIRTUAL_ENV

# Reactivate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# If still failing, recreate environment
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Permission Issues
**Problem**: Permission denied errors
```bash
$ python main.py bridge create
Permission denied: bridge creation requires root privileges
```

**Solution**:
```bash
# Use sudo for bridge operations
sudo python main.py bridge create

# Or run with virtual environment
sudo .venv/bin/python main.py bridge create

# Check file permissions
ls -la clab-tools.sh
chmod +x clab-tools.sh
```

### Configuration Issues

#### Configuration File Not Found
**Problem**: Configuration file not loaded
```bash
$ python main.py --config myconfig.yaml data show
✗ Error: Configuration file not found: myconfig.yaml
```

**Solution**:
```bash
# Use absolute path
python main.py --config /full/path/to/myconfig.yaml data show

# Check current directory
ls -la *.yaml

# Use default configuration
cp config.yaml myconfig.yaml
```

#### Invalid Configuration
**Problem**: Configuration validation errors
```bash
✗ Error: Log level must be one of: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
```

**Solution**:
```bash
# Check configuration syntax
python -c "
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
    print('Configuration syntax is valid')
"

# Validate against schema
python -c "
from clab_tools.config import get_settings
try:
    settings = get_settings('config.yaml')
    print('Configuration is valid')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

#### Environment Variable Issues
**Problem**: Environment variables not recognized
```bash
$ export CLAB_DATABASE_URL="sqlite:///test.db"
$ python main.py data show
# Still using default database
```

**Solution**:
```bash
# Check variable format
env | grep CLAB_

# Ensure correct naming
export CLAB_DATABASE_URL="sqlite:///test.db"  # Correct
export CLAB_DB_URL="sqlite:///test.db"        # Incorrect

# Test variable loading
python -c "
import os
print('CLAB_DATABASE_URL:', os.getenv('CLAB_DATABASE_URL'))
"
```

### Database Issues

#### Database Connection Failures
**Problem**: Cannot connect to database
```bash
✗ Error: Database operation failed: health_check (Details: {'operation': 'health_check', 'original_error': 'database is locked'})
```

**Solution**:
```bash
# Check database file permissions
ls -la clab_topology.db

# Try different database
python main.py --db-url "sqlite:///temp.db" data show

# Check for lock files
ls -la *.db-*

# Remove lock files (if safe)
rm -f clab_topology.db-wal clab_topology.db-shm

# Test with in-memory database
python main.py --db-url "sqlite:///:memory:" data show
```

#### Database Schema Issues
**Problem**: Table doesn't exist errors
```bash
✗ Error: Database operation failed: (sqlite3.OperationalError) no such table: nodes
```

**Solution**:
```bash
# Let the application create tables automatically
python main.py data show

# Or manually recreate database
rm -f clab_topology.db
python main.py data show

# Check database schema
sqlite3 clab_topology.db ".schema"
```

#### PostgreSQL/MySQL Connection Issues
**Problem**: Remote database connection failures
```bash
✗ Error: Database operation failed: (psycopg2.OperationalError) could not connect to server
```

**Solution**:
```bash
# Test basic connectivity
ping database-host

# Test port connectivity
telnet database-host 5432

# Verify credentials
psql -h database-host -U username -d database

# Check connection string format
export CLAB_DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Enable connection debugging
python main.py --debug --db-url "postgresql://user:pass@host/db" data show
```

### CSV Import Issues

#### File Not Found
**Problem**: CSV files cannot be found
```bash
✗ Error: File not found: nodes.csv
```

**Solution**:
```bash
# Check file exists
ls -la nodes.csv connections.csv

# Use absolute paths
python main.py data import -n /full/path/to/nodes.csv -c /full/path/to/connections.csv

# Check current directory
pwd
ls -la *.csv
```

#### CSV Format Issues
**Problem**: Missing required columns
```bash
✗ Error: Missing required column 'node_name' in nodes.csv
```

**Solution**:
```bash
# Check CSV headers
head -1 nodes.csv
head -1 connections.csv

# Verify column names match exactly
cat nodes.csv | head -5

# Check for BOM or encoding issues
file nodes.csv
hexdump -C nodes.csv | head -1

# Convert encoding if needed
iconv -f UTF-8-BOM -t UTF-8 nodes.csv > nodes_clean.csv
```

#### Data Validation Errors
**Problem**: Invalid data in CSV files
```bash
✗ Error: Invalid IP address format: '10.0.0'
```

**Solution**:
```bash
# Enable debug mode for detailed errors
python main.py --debug data import -n nodes.csv -c connections.csv

# Validate CSV data manually
python -c "
import pandas as pd
df = pd.read_csv('nodes.csv')
print('Columns:', df.columns.tolist())
print('Data types:', df.dtypes)
print('Sample data:')
print(df.head())
"

# Check for special characters
grep -P '[^\x00-\x7F]' nodes.csv
```

### Topology Generation Issues

#### Template Errors
**Problem**: Jinja2 template errors
```bash
✗ Error: Template error: 'node' object has no attribute 'invalid_field'
```

**Solution**:
```bash
# Check template syntax
python -c "
from jinja2 import Template
with open('topology_template.j2') as f:
    template = Template(f.read())
    print('Template syntax is valid')
"

# Use default template
cp topology_template.j2 topology_template.j2.backup
git checkout topology_template.j2

# Debug template variables
python main.py --debug topology generate -o test.yml
```

#### YAML Validation Errors
**Problem**: Generated YAML is invalid
```bash
✗ Error: Generated YAML validation failed
```

**Solution**:
```bash
# Generate without validation
python main.py topology generate -o test.yml

# Check YAML syntax
python -c "
import yaml
with open('test.yml') as f:
    data = yaml.safe_load(f)
    print('YAML is valid')
"

# Use YAML linter
yamllint test.yml
```

### Bridge Management Issues

#### Bridge Creation Failures
**Problem**: Cannot create bridges
```bash
✗ Error: Bridge creation failed: Command 'ip link add br-test type bridge' failed
```

**Solution**:
```bash
# Check root privileges
sudo -v

# Verify ip command availability
which ip
ip link help

# Check existing bridges
ip link show type bridge

# Try manual bridge creation
sudo ip link add test-br type bridge
sudo ip link delete test-br

# Use dry-run mode for debugging
python main.py bridge create --dry-run
```

#### Bridge Cleanup Issues
**Problem**: Cannot remove bridges
```bash
✗ Error: Bridge cleanup failed: bridge still has interfaces
```

**Solution**:
```bash
# Check bridge interfaces
ip link show type bridge

# List bridge details
bridge link show

# Manual cleanup
sudo ip link set br-name down
sudo ip link delete br-name

# Force cleanup
python main.py cleanup-bridges --force
```

### Logging Issues

#### Log File Permission Errors
**Problem**: Cannot write to log file
```bash
✗ Error: Permission denied: '/var/log/clab/clab.log'
```

**Solution**:
```bash
# Create log directory
sudo mkdir -p /var/log/clab
sudo chown $USER:$USER /var/log/clab

# Use local log file
mkdir -p logs
# Update config.yaml:
# logging:
#   file_path: "logs/clab.log"

# Disable file logging
# logging:
#   file_path: null
```

#### Log Format Issues
**Problem**: Unexpected log format
```bash
# Logs appear as raw JSON instead of formatted
```

**Solution**:
```bash
# Check log format setting
python main.py --log-format console data show

# Verify configuration
grep -A 5 "logging:" config.yaml

# Test different formats
python main.py --log-format json data show
python main.py --log-format console data show
```

## Performance Issues

### Slow CSV Import
**Problem**: CSV import takes too long
```bash
# Import seems to hang on large files
```

**Solution**:
```bash
# Enable debug mode to see progress
python main.py --debug data import -n large_nodes.csv -c large_connections.csv

# Check file sizes
wc -l *.csv
ls -lh *.csv

# Process smaller batches
split -l 1000 large_nodes.csv nodes_batch_
# Import each batch separately

# Monitor system resources
top
df -h
```

### Memory Usage Issues
**Problem**: High memory usage or out-of-memory errors
```bash
MemoryError: Unable to allocate array
```

**Solution**:
```bash
# Monitor memory usage
python main.py --debug data import -n nodes.csv -c connections.csv &
top -p $!

# Use streaming processing for large files
# (Feature available in code - check pandas chunksize)

# Increase system memory or use smaller datasets
# Split large CSV files into smaller chunks
```

### Database Performance Issues
**Problem**: Slow database operations
```bash
# Queries take too long to complete
```

**Solution**:
```bash
# Enable SQL debugging
# In config.yaml:
# database:
#   echo: true

# Check database file size
ls -lh clab_topology.db

# Optimize database (SQLite)
sqlite3 clab_topology.db "VACUUM;"
sqlite3 clab_topology.db "ANALYZE;"

# Consider using PostgreSQL for better performance
export CLAB_DATABASE_URL="postgresql://user:pass@localhost/clab"
```

## Advanced Debugging

### Debug Mode Analysis
```bash
# Enable comprehensive debugging
python main.py --debug --log-level DEBUG --log-format json data import -n nodes.csv -c connections.csv

# Save debug output
python main.py --debug data show 2>&1 | tee debug.log

# Analyze debug output
grep "ERROR" debug.log
grep "Database" debug.log
```

### System Information Gathering
```bash
# Collect system information
cat > debug_info.sh << 'EOF'
#!/bin/bash
echo "=== System Information ==="
uname -a
python --version
pip list

echo -e "\n=== Environment Variables ==="
env | grep CLAB_ | sort

echo -e "\n=== File Permissions ==="
ls -la *.csv *.yaml *.db 2>/dev/null

echo -e "\n=== Disk Space ==="
df -h .

echo -e "\n=== Memory Usage ==="
free -h

echo -e "\n=== Network Interfaces ==="
ip link show 2>/dev/null || ifconfig -a

echo -e "\n=== Containerlab Version ==="
clab version 2>/dev/null || echo "Containerlab not installed"
EOF

chmod +x debug_info.sh
./debug_info.sh > debug_info.txt
```

### Log Analysis Tools
```bash
# Analyze JSON logs
python main.py --log-format json data show | jq '.'

# Filter specific log levels
python main.py --debug data show 2>&1 | grep "ERROR"

# Extract timing information
python main.py --debug data show 2>&1 | grep "duration"

# Count log entries by level
python main.py --debug data show 2>&1 | grep -o '"level":"[^"]*"' | sort | uniq -c
```

## Getting Help

### Self-Help Resources
1. **Check Documentation**: Review relevant docs section
2. **Enable Debug Mode**: Use `--debug` flag for detailed output
3. **Test with Minimal Data**: Try with small, known-good CSV files
4. **Verify Configuration**: Test with default settings

### Information to Gather
When reporting issues, include:
- Complete error message and stack trace
- Command that failed (with `--debug` output)
- Configuration file (sanitized of sensitive data)
- Sample CSV files (if related to import)
- System information (`debug_info.txt` from above)
- Python and dependency versions (`pip list`)

### Common Solutions Summary
- **File not found**: Use absolute paths, check current directory
- **Permission denied**: Use `sudo` for bridge operations, check file permissions
- **Database locked**: Remove lock files, check for multiple processes
- **Invalid configuration**: Validate YAML syntax and schema
- **Memory issues**: Process smaller files, monitor system resources
- **Template errors**: Verify template syntax, use default template
- **Network issues**: Check connectivity, verify credentials

For additional help:
- Check [GitHub Issues](repository-url/issues)
- Review [User Guide](user-guide.md)
- Consult [Configuration Guide](configuration.md)
- See [Developer Guide](developer-guide.md) for advanced debugging

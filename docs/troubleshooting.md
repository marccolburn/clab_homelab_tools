# Troubleshooting Guide

Common issues and solutions for the Containerlab Homelab Tools.

## Quick Diagnosis

### Check System Status
```bash
# Verify Python version
python --version

# Check virtual environment
which python
echo $VIRTUAL_ENV

# Test basic functionality
python main.py --help

# Run health check
python main.py --debug show-data
```

## Common Issues

### Installation Problems

#### Python Version Issues
**Problem**: `python` command not found or wrong version
```bash
$ python main.py --help
-bash: python: command not found
```

**Solution**:
```bash
# Use python3 explicitly
python3 main.py --help

# Or create alias
alias python=python3

# Check available Python versions
ls /usr/bin/python*
```

#### Virtual Environment Issues
**Problem**: Dependencies not found or version conflicts
```bash
$ python main.py --help
ModuleNotFoundError: No module named 'click'
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
$ python main.py create-bridges
Permission denied: bridge creation requires root privileges
```

**Solution**:
```bash
# Use sudo for bridge operations
sudo python main.py create-bridges

# Or run with virtual environment
sudo .venv/bin/python main.py create-bridges

# Check file permissions
ls -la clab-tools.sh
chmod +x clab-tools.sh
```

### Configuration Issues

#### Configuration File Not Found
**Problem**: Configuration file not loaded
```bash
$ python main.py --config myconfig.yaml show-data
✗ Error: Configuration file not found: myconfig.yaml
```

**Solution**:
```bash
# Use absolute path
python main.py --config /full/path/to/myconfig.yaml show-data

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
$ python main.py show-data
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
python main.py --db-url "sqlite:///temp.db" show-data

# Check for lock files
ls -la *.db-*

# Remove lock files (if safe)
rm -f clab_topology.db-wal clab_topology.db-shm

# Test with in-memory database
python main.py --db-url "sqlite:///:memory:" show-data
```

#### Database Schema Issues
**Problem**: Table doesn't exist errors
```bash
✗ Error: Database operation failed: (sqlite3.OperationalError) no such table: nodes
```

**Solution**:
```bash
# Let the application create tables automatically
python main.py show-data

# Or manually recreate database
rm -f clab_topology.db
python main.py show-data

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
python main.py --debug --db-url "postgresql://user:pass@host/db" show-data
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
python main.py import-csv -n /full/path/to/nodes.csv -c /full/path/to/connections.csv

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
python main.py --debug import-csv -n nodes.csv -c connections.csv

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
python main.py --debug generate-topology -o test.yml
```

#### YAML Validation Errors
**Problem**: Generated YAML is invalid
```bash
✗ Error: Generated YAML validation failed
```

**Solution**:
```bash
# Generate without validation
python main.py generate-topology -o test.yml

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
python main.py create-bridges --dry-run
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
python main.py --log-format console show-data

# Verify configuration
grep -A 5 "logging:" config.yaml

# Test different formats
python main.py --log-format json show-data
python main.py --log-format console show-data
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
python main.py --debug import-csv -n large_nodes.csv -c large_connections.csv

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
python main.py --debug import-csv -n nodes.csv -c connections.csv &
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
python main.py --debug --log-level DEBUG --log-format json import-csv -n nodes.csv -c connections.csv

# Save debug output
python main.py --debug show-data 2>&1 | tee debug.log

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
python main.py --log-format json show-data | jq '.'

# Filter specific log levels
python main.py --debug show-data 2>&1 | grep "ERROR"

# Extract timing information
python main.py --debug show-data 2>&1 | grep "duration"

# Count log entries by level
python main.py --debug show-data 2>&1 | grep -o '"level":"[^"]*"' | sort | uniq -c
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

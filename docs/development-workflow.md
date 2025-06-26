# Development Workflow

**📊 VISUAL WORKFLOWS: See [Project Workflows & Architecture](workflows-and-architecture.md) for comprehensive diagrams showing user workflows, developer processes, and CI/CD pipelines.**

This document outlines the development workflow for the Containerlab Homelab Tools project using trunk-based development.

## Trunk-Based Development Model

We follow a **trunk-based development** approach where:
- All developers work on short-lived feature branches
- Feature branches are merged directly to `main`
- The `main` branch is always deployable
- Releases are tagged from `main`
- Hotfixes go directly to `main`

## Branch Strategy

### Main Branch
- **`main`**: The single source of truth
  - Always in a deployable state
  - Protected with branch protection rules
  - All changes go through pull requests
  - CI/CD runs on every push and PR

### Feature Branches
- **`feature/short-description`**: Short-lived branches (1-3 days max)
- **`fix/issue-description`**: Bug fixes
- **`docs/update-description`**: Documentation updates

### No Long-Lived Branches
- No `develop` or `staging` branches
- No release branches (use tags instead)
- Feature flags for incomplete features if needed

## Local Development Setup

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/marccolburn/clab_homelab_tools.git
cd clab_homelab_tools

# Run the development setup script
./scripts/setup-dev.sh

# This will:
# - Create virtual environment
# - Install dependencies
# - Set up pre-commit hooks
# - Run initial tests
```

### Daily Development Workflow

```bash
# 1. Start with latest main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/add-new-feature

# 3. Make changes and commit frequently
git add .
git commit -m "Add initial implementation"

# Pre-commit hooks will run automatically:
# - Code formatting (black)
# - Import sorting (isort)
# - Linting (flake8)
# - YAML validation
# - Trailing whitespace removal

# 4. Push branch and create PR
git push origin feature/add-new-feature
# Create PR via GitHub UI
```

## Pre-Commit Process

### Automated Checks
Pre-commit hooks run automatically on every commit:

```bash
# To run manually on all files
pre-commit run --all-files

# To run specific hooks
pre-commit run black
pre-commit run flake8
```

### What Gets Checked
- **Code formatting**: Black automatically formats Python code
- **Import sorting**: isort organizes imports
- **Linting**: flake8 checks for style violations
- **YAML validation**: Ensures config files are valid
- **File cleanup**: Removes trailing whitespace, ensures final newlines

### If Pre-Commit Fails
```bash
# Fix issues automatically where possible
black clab_tools/ tests/
isort clab_tools/ tests/

# Check what needs manual fixing
flake8 clab_tools/ tests/

# Stage fixed files and commit again
git add .
git commit -m "Fix code formatting and linting issues"
```

## Testing Strategy

### Local Testing Before Committing

```bash
# Run full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=clab_tools --cov-report=html

# Run specific test categories
pytest tests/test_csv_import.py -v
pytest tests/integration/ -v

# Test the CLI installation
./install-cli.sh
clab-tools --help
```

### Test Requirements
- All new code must have tests
- Maintain >85% test coverage
- Integration tests for CLI workflows
- Tests must pass on Python 3.8-3.11

## Pull Request Process

### Creating a Pull Request

1. **Ensure branch is up to date**:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/your-branch
   git rebase main  # or merge if you prefer
   ```

2. **Run full test suite locally**:
   ```bash
   pytest tests/ -v --cov=clab_tools
   ```

3. **Push and create PR**:
   ```bash
   git push origin feature/your-branch
   ```

4. **Create PR with good description**:
   - Clear title summarizing the change
   - Description of what changed and why
   - Link to relevant issues
   - Screenshots for UI changes
   - Test instructions if needed

### PR Requirements

✅ **Required Checks** (enforced by GitHub):
- All CI tests pass (Ubuntu + macOS, Python 3.8-3.11)
- Code coverage doesn't decrease
- Integration tests pass
- Pre-commit hooks pass

✅ **Review Requirements**:
- At least 1 approval (for team environments)
- All conversations resolved
- Branch is up to date with main

### PR Best Practices

- **Keep PRs small**: <400 lines of code when possible
- **Single responsibility**: One feature/fix per PR
- **Good commit messages**: Use conventional commits format
- **Self-review**: Review your own PR before requesting review
- **Update documentation**: Include doc updates in the same PR

## CI/CD Pipeline

### Continuous Integration (CI)

**Triggers**: Every push to `main`, every PR to `main`

**What Gets Tested**:
- Matrix testing: Ubuntu + macOS × Python 3.8-3.11
- Unit tests with coverage reporting
- Integration tests (CLI workflows)
- Code quality checks
- Security scanning (weekly)

**Pipeline Steps**:
1. **Setup**: Install Python and dependencies
2. **Test**: Run pytest with coverage
3. **Integration**: Test CLI installation and basic workflows
4. **Coverage**: Upload coverage to Codecov
5. **Artifacts**: Store test results and coverage reports

### Continuous Deployment (CD)

**Automatic Deployment**:
- Every push to `main` after successful CI
- Creates deployable artifacts
- Updates documentation (if configured)

**Release Process**:
```bash
# Create and push a tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# GitHub Actions will:
# 1. Run full CI pipeline
# 2. Create GitHub release
# 3. Build distribution packages
# 4. Upload release artifacts
```

## Hotfix Process

For urgent fixes that need to bypass normal workflow:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b fix/critical-security-issue

# 2. Make minimal fix
# Edit files...
git add .
git commit -m "fix: resolve critical security vulnerability"

# 3. Push and create emergency PR
git push origin fix/critical-security-issue
# Create PR with "hotfix" label

# 4. Fast-track review and merge
# 5. Tag and release immediately
git tag -a v1.2.4 -m "Hotfix: critical security patch"
git push origin v1.2.4
```

## Configuration Management

### Environment-Specific Config

```bash
# Development
cp config.yaml config-dev.yaml
# Edit for local development

# Production (on server)
cp config.yaml config-prod.yaml
# Edit for production settings
```

### Secrets Management

**Never commit**:
- Database passwords
- API keys
- Private configuration
- Production URLs

**Use instead**:
- Environment variables
- GitHub Secrets (for CI/CD)
- External secret management

## Quality Gates

### Before Merging to Main

✅ **Automated Checks**:
- All tests pass
- Coverage ≥85%
- No linting errors
- Security scan passes
- Integration tests pass

✅ **Manual Checks**:
- Code review completed
- Documentation updated
- Breaking changes documented
- Manual testing on local system

### Release Criteria

✅ **Quality Requirements**:
- All tests passing
- No known critical bugs
- Documentation up to date
- Performance benchmarks met
- Security review completed

## Monitoring and Maintenance

### Regular Maintenance Tasks

**Weekly**:
- Review and update dependencies
- Check security scan results
- Review test coverage trends
- Monitor CI/CD performance

**Monthly**:
- Update development dependencies
- Review and update documentation
- Performance optimization review
- Clean up stale branches

### Metrics to Track

- **Test coverage percentage**
- **CI/CD pipeline duration**
- **Time from PR creation to merge**
- **Number of reverts/hotfixes**
- **Code quality trends**

## Common Commands Reference

### Development Setup
```bash
./scripts/setup-dev.sh              # Initial setup
source .venv/bin/activate           # Activate environment
```

### Testing
```bash
pytest tests/ -v                    # Run tests
pytest tests/ --cov=clab_tools      # Run with coverage
pytest tests/integration/           # Integration tests only
```

### Code Quality
```bash
black clab_tools/ tests/            # Format code
isort clab_tools/ tests/            # Sort imports
flake8 clab_tools/ tests/           # Lint code
pre-commit run --all-files          # Run all hooks
```

### Git Workflow
```bash
git checkout main && git pull       # Update main
git checkout -b feature/name        # Create feature branch
git add . && git commit -m "msg"    # Commit changes
git push origin feature/name        # Push branch
```

### CLI Testing
```bash
./install-cli.sh                    # Install CLI
clab-tools --help                   # Test CLI
clab-tools import-csv -n nodes.csv -c connections.csv  # Test workflow
```

## Troubleshooting

### Common Issues

**Pre-commit hooks failing**:
```bash
# Update hooks
pre-commit autoupdate
pre-commit install

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

**Tests failing locally**:
```bash
# Clean environment
rm -rf .pytest_cache/
rm -f clab_topology.db

# Reinstall dependencies
pip install -r requirements.txt
pytest tests/ -v
```

**CI failing but tests pass locally**:
- Check Python version differences
- Verify all dependencies in requirements.txt
- Check for OS-specific issues (macOS vs Linux)
- Review CI logs for specific errors

For more troubleshooting help, see [docs/troubleshooting.md](docs/troubleshooting.md).

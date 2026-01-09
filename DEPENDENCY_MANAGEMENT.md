# Dependency Management Plan

This document outlines the strategy for managing dependencies in the expense-tracker-backend project.

## Overview

The project uses `pyproject.toml` for dependency management following PEP 621 standards. Dependencies are organized into:
- **Core dependencies**: Required for the application to run
- **Dev dependencies**: Development tools (testing, linting, formatting)
- **Production dependencies**: Production-specific packages (monitoring, deployment)

## Tools

### 1. pip
Primary package manager for Python packages.

### 2. Dependency Checking Scripts
- `scripts/check_dependencies.py`: Automated dependency checking script
- `pipdeptree`: Visualize dependency tree
- `safety`: Check for known security vulnerabilities

## Dependency Update Process

### Regular Checks (Monthly)

1. **Check for outdated packages**
   ```bash
   python scripts/check_dependencies.py
   ```

2. **Manual check with pip**
   ```bash
   pip list --outdated
   ```

3. **Check dependency tree**
   ```bash
   pip install pipdeptree
   pipdeptree
   ```

4. **Security vulnerability scan**
   ```bash
   pip install safety
   safety check
   ```

### Update Workflow

#### Step 1: Review Updates
- Check changelogs for breaking changes
- Review release notes for major/minor updates
- Identify security patches in patch updates

#### Step 2: Update pyproject.toml
- Update version numbers in `[project]` dependencies
- Update version numbers in `[project.optional-dependencies]`
- Document any breaking changes in commit message

#### Step 3: Install Updated Dependencies
```bash
# For development
pip install --upgrade -e '.[dev]'

# For production
pip install --upgrade -e '.[production]'
```

#### Step 4: Test
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Check for deprecation warnings
pytest -W default::DeprecationWarning
```

#### Step 5: Update Lock File (if using)
If using a lock file system (pip-tools, poetry lock):
```bash
pip-compile pyproject.toml
# or
poetry lock --no-update
```

## Dependency Categories

### Core Dependencies
- **FastAPI**: Web framework (0.109.0)
- **SQLAlchemy**: ORM (2.0.25)
- **Alembic**: Database migrations (1.13.1)
- **Redis**: Caching (5.0.1)
- **Celery**: Background tasks (5.3.6)
- **Pydantic**: Data validation (2.5.3)

### Security Dependencies
- **python-jose**: JWT handling (3.3.0)
- **passlib**: Password hashing (1.7.4)
- **cryptography**: Cryptographic primitives (42.0.0)

### Infrastructure
- **boto3**: AWS S3 integration (1.34.34)
- **psycopg2-binary**: PostgreSQL driver (2.9.9)

### Development Tools
- **pytest**: Testing framework (7.4.4)
- **black**: Code formatting (24.1.1)
- **mypy**: Type checking (1.8.0)
- **flake8**: Linting (7.0.0)

## Version Pinning Strategy

### Strict Pinning
All dependencies use exact versions (`==`) to ensure reproducible builds:
```toml
dependencies = [
    "fastapi[all]==0.109.0",
    "sqlalchemy==2.0.25",
]
```

### When to Update

#### Immediate Updates (Security)
- Security vulnerabilities in current versions
- Critical bug fixes
- Zero-day exploits

#### Scheduled Updates (Monthly)
- Patch versions (bug fixes)
- Minor versions (new features, backward compatible)
- Development tool updates

#### Planned Updates (Quarterly)
- Major versions (breaking changes)
- Framework upgrades (requires testing and migration)
- Infrastructure changes

## Security Considerations

### Vulnerability Scanning
Run weekly security checks:
```bash
safety check
pip-audit
```

### Known Vulnerabilities
- Monitor CVE databases
- Subscribe to security advisories
- Set up Dependabot (GitHub) or similar

### Patching Process
1. Identify vulnerable package
2. Check if patch version exists
3. Update pyproject.toml
4. Test thoroughly
5. Deploy immediately if critical

## Automated Tools

### Pre-commit Hooks
Include dependency checks in pre-commit hooks:
```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.6
  hooks:
    - id: bandit
- repo: https://github.com/pyupio/safety
  rev: 2.3.4
  hooks:
    - id: safety
```

### CI/CD Integration
Add to GitHub Actions workflow:
```yaml
- name: Check dependencies
  run: |
    pip install safety pipdeptree
    safety check
    python scripts/check_dependencies.py
```

## Troubleshooting

### Dependency Conflicts
```bash
pip check
pipdeptree --warn fail
```

### Resolve Conflicts
1. Identify conflicting packages
2. Check compatible versions
3. Update pyproject.toml
4. Test resolution: `pip install -e '.[dev]'`

### Lock File Regeneration
If using pip-tools:
```bash
pip-compile --upgrade pyproject.toml
```

## Best Practices

1. **Always pin versions**: Use `==` for exact versions
2. **Document breaking changes**: Keep CHANGELOG.md updated
3. **Test before updating**: Never update production without testing
4. **Review dependencies**: Remove unused packages regularly
5. **Security first**: Prioritize security patches
6. **Version bumps**: Follow semantic versioning understanding

## Resources

- [PyPI](https://pypi.org/): Python Package Index
- [Safety DB](https://github.com/pyupio/safety-db): Security vulnerability database
- [Dependabot](https://dependabot.com/): Automated dependency updates
- [pip-audit](https://github.com/pypa/pip-audit): Security auditing tool


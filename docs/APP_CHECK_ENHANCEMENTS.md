# TopDeck App and Check Enhancements

This document describes the enhanced app and check functionality added to TopDeck.

## App Enhancements

The TopDeck app (`make run` or `python -m topdeck`) now supports comprehensive CLI arguments:

### Usage

```bash
# Show help
python -m topdeck --help
make run-help

# Show version
python -m topdeck --version

# Start with custom port
python -m topdeck --port 8080

# Start on localhost only
python -m topdeck --host 127.0.0.1

# Enable debug logging
python -m topdeck --log-level DEBUG

# Disable auto-reload
python -m topdeck --no-reload

# Enable auto-reload explicitly
python -m topdeck --reload

# Run with multiple workers (production)
python -m topdeck --workers 4 --no-reload
```

### Available CLI Options

- `--help, -h`: Show help message and exit
- `--version`: Show program version and exit
- `--host HOST`: Bind socket to this host (default: 0.0.0.0)
- `--port PORT`: Bind socket to this port (default: 8000)
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Logging level (default: INFO)
- `--reload`: Enable auto-reload (overrides environment setting)
- `--no-reload`: Disable auto-reload (overrides environment setting)
- `--workers WORKERS`: Number of worker processes (default: 1)

## Check Enhancements

The `make check` target has been enhanced with additional functionality:

### Standard Check (Quick)

```bash
make check
```

Runs:
1. **Linting** with ruff and black
2. **Type checking** with mypy
3. **Tests** with pytest and coverage

### Comprehensive Check

```bash
make check-all
```

Runs everything in `make check` plus:
4. **Security checks** with bandit and safety

### Individual Check Targets

```bash
# Run only linting
make lint

# Run only type checking
make type-check

# Run only tests
make test

# Run only security checks
make security

# Format code
make format
```

## Health Check Utility

A new health check script has been added to verify the API server is running:

### Usage

```bash
# Basic health check
make health-check
python scripts/health_check.py

# Detailed health check (includes Neo4j, Redis, RabbitMQ)
make health-check-detailed
python scripts/health_check.py --detailed

# Custom host/port
python scripts/health_check.py --host localhost --port 8080

# With timeout
python scripts/health_check.py --timeout 10
```

### Health Check Options

- `--host HOST`: API host (default: localhost)
- `--port PORT`: API port (default: 8000)
- `--detailed`: Show detailed health information including service dependencies
- `--timeout TIMEOUT`: Request timeout in seconds (default: 5)

## New Makefile Targets

All new targets added:

```bash
make help                  # Show all available targets (updated)
make run-help              # Show API server help
make health-check          # Quick API health check
make health-check-detailed # Detailed API health check
make security              # Run security checks only
make check                 # Standard checks (lint, type-check, test)
make check-all             # All checks including security
```

## Security Checks

The security check target includes:

1. **Bandit**: Scans Python code for common security issues
   - SQL injection vulnerabilities
   - Hardcoded passwords
   - Use of insecure functions
   - Shell injection risks

2. **Safety**: Checks dependencies for known vulnerabilities
   - CVE database scanning
   - Vulnerability reporting
   - Dependency tree analysis

To install security tools:

```bash
pip install bandit safety
```

## Benefits

### App Enhancements
- ✅ **Better DevOps**: Easier configuration in different environments
- ✅ **Debugging**: Quick log level changes without environment variables
- ✅ **Production Ready**: Worker process support for scalability
- ✅ **Developer Friendly**: Auto-reload control for development
- ✅ **Documentation**: Built-in help with examples

### Check Enhancements
- ✅ **Security**: Proactive vulnerability detection
- ✅ **Flexibility**: Run specific checks or all at once
- ✅ **CI/CD Ready**: Easy integration into pipelines
- ✅ **Fast Feedback**: Quick `check` for local development
- ✅ **Comprehensive**: `check-all` for pre-commit/pre-push

### Health Check
- ✅ **Monitoring**: Quick status verification
- ✅ **Debugging**: Detailed dependency health
- ✅ **Automation**: Scriptable for health monitoring
- ✅ **CI/CD**: Integration test validation

## CI/CD Integration Examples

### GitHub Actions

```yaml
- name: Run comprehensive checks
  run: make check-all

- name: Verify API health
  run: |
    make run &
    sleep 10
    make health-check
```

### Pre-commit Hook

```yaml
repos:
  - repo: local
    hooks:
      - id: topdeck-check
        name: TopDeck Checks
        entry: make check
        language: system
        pass_filenames: false
```

## Migration Guide

### Before
```bash
# Limited control
python -m topdeck

# Only environment-based configuration
export APP_PORT=8080
python -m topdeck
```

### After
```bash
# Full CLI control
python -m topdeck --port 8080 --log-level DEBUG --workers 4

# Or use Makefile shortcuts
make run-help
make health-check-detailed
make check-all
```

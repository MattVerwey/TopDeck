# TopDeck CLI Quick Reference

Quick reference for the enhanced TopDeck CLI and Makefile commands.

## 🚀 Running the App

```bash
# Show help
python -m topdeck --help
make run-help

# Show version
python -m topdeck --version

# Start with defaults (0.0.0.0:8000)
make run
python -m topdeck

# Custom port
python -m topdeck --port 8080

# Custom host (localhost only)
python -m topdeck --host 127.0.0.1

# Debug mode
python -m topdeck --log-level DEBUG

# Production mode (4 workers, no reload)
python -m topdeck --workers 4 --no-reload

# Development with reload
python -m topdeck --reload --log-level DEBUG
```

## ✅ Quality Checks

```bash
# Quick check (lint + type-check + test)
make check

# Comprehensive (includes security)
make check-all

# Individual checks
make lint          # Code style
make type-check    # Type checking
make test          # Run tests
make security      # Security scan
make format        # Auto-format code
```

## 🏥 Health Checks

```bash
# Quick health check
make health-check
python scripts/health_check.py

# Detailed (includes Neo4j, Redis, RabbitMQ)
make health-check-detailed
python scripts/health_check.py --detailed

# Custom endpoint
python scripts/health_check.py --host localhost --port 8080
```

## 🐳 Docker Services

```bash
# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs
```

## 🧹 Cleanup

```bash
# Clean generated files
make clean
```

## 📦 Installation

```bash
# Production dependencies
make install

# Development dependencies (includes linters, testers)
make install-dev
```

## 💡 Common Workflows

### Local Development
```bash
# 1. Start services
make docker-up

# 2. Run app with auto-reload
python -m topdeck --reload --log-level DEBUG

# 3. In another terminal, check health
make health-check-detailed

# 4. Make changes, run checks
make check

# 5. Before commit
make check-all
```

### Production Deployment
```bash
# Run with multiple workers
python -m topdeck \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-reload \
  --log-level INFO
```

### CI/CD Pipeline
```bash
# Full validation
make check-all

# Start server for integration tests
make run &
sleep 10
make health-check

# Or use the script directly
python scripts/health_check.py --timeout 30
```

## 🔧 All Available Makefile Targets

```bash
help                  # Show all targets
install               # Install production deps
install-dev           # Install dev deps
test                  # Run tests with coverage
test-fast             # Run tests without coverage
lint                  # Run linters
format                # Auto-format code
type-check            # Run type checking
security              # Run security checks
clean                 # Clean up files
run                   # Run API server
run-help              # Show API help
health-check          # Quick health check
health-check-detailed # Detailed health check
docker-up             # Start Docker services
docker-down           # Stop Docker services
docker-logs           # Show Docker logs
check                 # Standard checks
check-all             # All checks + security
```

## 📖 More Information

- Full documentation: [docs/APP_CHECK_ENHANCEMENTS.md](docs/APP_CHECK_ENHANCEMENTS.md)
- Enhancement summary: [ENHANCEMENT_SUMMARY.md](ENHANCEMENT_SUMMARY.md)
- Main README: [README.md](README.md)

# TopDeck Development Guide

This guide covers the development setup and workflows for TopDeck.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for Neo4j, Redis, RabbitMQ)
- Git

## Technology Stack

Based on **ADR-001: Technology Stack Selection**, TopDeck uses:

**Backend:**
- Python 3.11+ with FastAPI
- AsyncIO for concurrency
- Pydantic for data validation

**Frontend:**
- React 18+ with TypeScript
- Vite for build tooling

**Storage:**
- Neo4j 5.x (Graph database)
- Redis 7.x (Cache)
- RabbitMQ 3.x (Message queue)

**Cloud SDKs:**
- Azure SDK for Python
- Boto3 (AWS)
- Google Cloud SDK

See [ADR-001](docs/architecture/adr/001-technology-stack.md) for the full rationale.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/MattVerwey/TopDeck.git
cd TopDeck
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install development dependencies
make install-dev

# Or manually:
pip install -r requirements-dev.txt
pre-commit install
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Start Infrastructure Services

```bash
make docker-up
```

This starts:
- Neo4j at http://localhost:7474 (bolt://localhost:7687)
- Redis at localhost:6379
- RabbitMQ at http://localhost:15672 (Management UI)

### 6. Run the API Server

```bash
make run

# Or manually:
PYTHONPATH=src python -m topdeck
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
make test

# Run tests without coverage (faster)
make test-fast

# Run specific test file
pytest tests/unit/test_api.py -v
```

### Code Quality

```bash
# Run all checks (lint, type-check, test)
make check

# Format code
make format

# Run linters
make lint

# Type checking
make type-check
```

### Pre-commit Hooks

Pre-commit hooks automatically run on `git commit`:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Black formatting
- Ruff linting
- MyPy type checking

To run manually:
```bash
pre-commit run --all-files
```

## Project Structure

```
TopDeck/
├── src/topdeck/           # Main application code
│   ├── api/               # FastAPI application and endpoints
│   ├── discovery/         # Cloud resource discovery engines
│   ├── integration/       # CI/CD platform integrations
│   ├── analysis/          # Topology and risk analysis
│   ├── storage/           # Database interfaces (Neo4j, Redis)
│   └── common/            # Shared utilities and config
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── docs/                  # Documentation
│   ├── architecture/      # Architecture docs and ADRs
│   ├── issues/            # Issue templates
│   └── pocs/              # Proof-of-concept implementations
├── scripts/               # Utility scripts
└── infrastructure/        # IaC and deployment configs
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write code following the existing patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
make check
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Common Tasks

### Adding a New Dependency

1. Add to `requirements.txt` (production) or `requirements-dev.txt` (development)
2. Install: `pip install -r requirements-dev.txt`
3. If it's a typed library, consider adding type stubs

### Creating a New Module

1. Create module directory: `src/topdeck/module_name/`
2. Add `__init__.py` with module docstring
3. Add tests: `tests/unit/test_module_name.py`
4. Update documentation

### Working with Neo4j

Access Neo4j Browser: http://localhost:7474
- Username: `neo4j`
- Password: `topdeck123` (from docker-compose.yml)

### Working with RabbitMQ

Access Management UI: http://localhost:15672
- Username: `topdeck`
- Password: `topdeck123`

### Debugging

Use ipdb for debugging:

```python
import ipdb; ipdb.set_trace()
```

Or use the built-in breakpoint:

```python
breakpoint()
```

## CI/CD

GitHub Actions workflows run on:
- Pull requests: lint, type-check, test
- Main branch: lint, type-check, test, build

## Documentation

- **ADRs**: Architecture Decision Records in `docs/architecture/adr/`
- **API Docs**: Auto-generated at `/api/docs` when server is running
- **Issue Templates**: Development issues in `docs/issues/`

## Troubleshooting

### Tests Failing

```bash
# Clean up cache and rerun
make clean
make test
```

### Import Errors

Make sure PYTHONPATH is set:
```bash
export PYTHONPATH=src
```

Or install the package in editable mode:
```bash
pip install -e .
```

### Docker Services Not Starting

```bash
# Stop and remove all containers
make docker-down
docker system prune

# Start fresh
make docker-up
```

### Type Checking Issues

If mypy complains about missing imports:
1. Check if type stubs are installed
2. Add to `[[tool.mypy.overrides]]` in `pyproject.toml` if needed

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

## Getting Help

- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Review existing issues in [docs/issues/](docs/issues/)
- Open a GitHub issue for bugs or feature requests
- Consult ADRs in `docs/architecture/adr/` for architecture decisions

# ADR-001: Technology Stack Selection

**Status**: Accepted  
**Date**: 2025-10-12  
**Decision Makers**: Development Team  
**Issue**: #1 - Technology Stack Decision

## Context

TopDeck is a multi-cloud integration and risk analysis platform that needs to:
- Discover and map cloud resources across Azure, AWS, and GCP
- Analyze dependencies and build topology graphs
- Provide real-time visualization and risk assessment
- Handle concurrent operations efficiently
- Scale horizontally to support multiple cloud environments
- Maintain high code quality and developer productivity

We need to select a technology stack that balances:
- **Performance**: Handle large-scale cloud resource discovery and graph operations
- **Developer Experience**: Enable rapid development and maintainability
- **Cloud SDK Quality**: Comprehensive, well-maintained SDKs for all cloud providers
- **Ecosystem**: Rich libraries for graph databases, API development, and data processing
- **Team Expertise**: Consider learning curve and available talent

## Decision

**We will use Python 3.11+ as the primary backend language with FastAPI as the web framework.**

This decision is complemented by:
- **Frontend**: React 18+ with TypeScript
- **Graph Database**: Neo4j 5.x
- **Cache**: Redis 7.x
- **Message Queue**: RabbitMQ 3.x
- **Container Orchestration**: Kubernetes

## Rationale

### Why Python Over Go

After creating proof-of-concept implementations in both Python and Go for Azure resource discovery, we evaluated both options against our key criteria:

#### 1. Cloud SDK Maturity and Quality

**Python Advantages:**
- **Azure SDK**: Comprehensive, actively maintained, excellent documentation
  - `azure-identity`, `azure-mgmt-resource`, `azure-mgmt-compute`, etc.
  - Pythonic APIs with async support
- **AWS SDK (Boto3)**: Industry-standard, mature, feature-complete
- **GCP SDK**: Well-maintained with extensive service coverage
- All major cloud providers prioritize Python SDKs with first-class support

**Go SDKs:**
- Good quality but generally trail behind Python in completeness
- Less extensive documentation and community examples
- Newer and evolving faster (more breaking changes)

**Winner**: Python - significantly better cloud SDK support across all three providers

#### 2. Development Velocity

**Python Advantages:**
- Rapid prototyping and iteration
- Less boilerplate code (compare: 250 lines in Python vs 350 lines in Go for same functionality)
- Dynamic typing with optional type hints for flexibility
- Rich ecosystem of data processing libraries
- Better debugging and REPL experience

**Go Advantages:**
- Strong compile-time type checking catches errors early
- Less runtime surprises
- Better IDE support for refactoring

**Winner**: Python - faster development cycles matter more for this project phase

#### 3. Performance

**Go Advantages:**
- Compiled language with superior raw performance
- Native concurrency with goroutines (no GIL limitations)
- Lower memory footprint
- Faster startup times

**Python Mitigations:**
- Async/await provides good concurrency for I/O-bound operations (which is our primary use case)
- Cloud API calls are network I/O bound, not CPU bound
- GIL is not a significant limitation for network operations
- Can optimize hot paths with Cython or Rust extensions if needed later

**Assessment**: Go has better raw performance, but Python is sufficient for our I/O-bound workload

#### 4. Ecosystem and Libraries

**Python Advantages:**
- Excellent Neo4j driver with async support
- FastAPI: Modern, high-performance web framework with OpenAPI generation
- Rich data processing libraries (Pandas, NumPy if needed)
- Extensive testing frameworks (pytest, coverage)
- Great async libraries (aiohttp, asyncio)

**Go Ecosystem:**
- Gin/Echo for web frameworks (good but less feature-rich than FastAPI)
- Neo4j driver available but less mature
- Smaller ecosystem overall

**Winner**: Python - richer ecosystem for our needs

#### 5. Code Maintainability

**Python Advantages:**
- Readable, clean syntax (follows "there should be one obvious way")
- Type hints improve code documentation
- Dataclasses reduce boilerplate
- Great linting and formatting tools (Black, Ruff, mypy)

**Go Advantages:**
- Forced error handling improves reliability
- Strong typing catches bugs at compile time
- Simpler language design with fewer ways to do things

**Assessment**: Both are maintainable, Python edges ahead for readability

#### 6. Team and Community

**Python Advantages:**
- Larger talent pool
- More cloud/DevOps engineers familiar with Python
- Extensive community support and examples
- Lower learning curve for new contributors

**Go:**
- Growing but smaller community
- Steeper learning curve for teams without Go experience

**Winner**: Python - easier hiring and onboarding

### POC Results

Both POCs demonstrated:
- Successful concurrent resource discovery
- Clean abstraction of cloud resources
- Simple dependency graph building

**Performance Comparison:**
- Python: 0.10s for discovering 7 resources with 6 concurrent tasks
- Go: 0.10s for discovering 7 resources with 6 concurrent goroutines
- **No significant performance difference for I/O-bound operations**

**Code Quality:**
- Python: More concise, easier to read (250 lines)
- Go: More verbose, explicit error handling (350 lines)

### Why Not Hybrid?

We considered a hybrid approach (Go for API, Python for discovery workers):

**Rejected because:**
- Adds operational complexity (two runtimes, two codebases)
- Increases deployment complexity
- Performance gains don't justify the overhead for our use case
- Harder to maintain and debug
- Team needs to maintain expertise in both languages

The simplicity and velocity of a single-language stack outweighs marginal performance benefits.

## Technology Stack Details

### Backend Stack

**Core:**
- **Python 3.11+**: Modern Python with performance improvements
- **FastAPI 0.104+**: High-performance web framework
  - Automatic OpenAPI documentation
  - Built-in async support
  - Pydantic for data validation
  - Excellent developer experience

**Cloud SDKs:**
- **Azure**: `azure-sdk-for-python` (latest)
- **AWS**: `boto3` (latest)
- **GCP**: `google-cloud-*` libraries (latest)

**Graph Database:**
- **Neo4j 5.x** with Python driver
- AsyncIO support for non-blocking operations

**API & Serialization:**
- **Pydantic**: Data validation and serialization
- **orjson**: Fast JSON serialization (if needed)

**Async Framework:**
- **asyncio**: Native Python async support
- **aiohttp**: Async HTTP client for API calls

**Testing:**
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Code coverage
- **httpx**: Async HTTP testing

### Frontend Stack

**Core:**
- **React 18+**: Modern UI library
- **TypeScript 5+**: Type safety for frontend
- **Vite**: Fast build tool and dev server

**Visualization:**
- **D3.js**: Data visualization
- **Cytoscape.js**: Graph/network visualization
- **Recharts**: Chart library

**State Management:**
- **TanStack Query (React Query)**: Server state management
- **Zustand**: Client state management (lightweight)

**UI Framework:**
- **Tailwind CSS**: Utility-first CSS
- **shadcn/ui**: Component library

### Infrastructure

**Storage:**
- **Neo4j 5.x**: Graph database for topology
- **Redis 7.x**: Caching and session storage
- **RabbitMQ 3.x**: Message queue for async tasks

**Deployment:**
- **Docker**: Containerization
- **Kubernetes**: Orchestration
- **Helm**: K8s package management

**Observability:**
- **Prometheus**: Metrics
- **Grafana**: Dashboards
- **OpenTelemetry**: Distributed tracing

## Consequences

### Positive

1. **Faster Development**: Python's expressiveness enables rapid feature development
2. **Better Cloud SDKs**: First-class support from all cloud providers
3. **Rich Ecosystem**: Extensive libraries for all our needs
4. **Easier Hiring**: Larger talent pool of Python developers
5. **Great Tooling**: Excellent development tools (linters, formatters, type checkers)
6. **Single Codebase**: Simpler maintenance and deployment

### Negative

1. **Performance Ceiling**: Go would be faster for CPU-bound operations
2. **GIL Limitations**: True parallelism requires multiprocessing (not needed for I/O-bound work)
3. **Runtime Errors**: Some errors only caught at runtime despite type hints
4. **Memory Usage**: Python uses more memory than Go

### Mitigations

1. **Performance**: 
   - Use async/await for I/O concurrency
   - Optimize hot paths if needed (Cython, Rust extensions)
   - Horizontal scaling handles load

2. **Type Safety**:
   - Use mypy strict mode in CI/CD
   - Comprehensive type hints
   - Pydantic for runtime validation

3. **Memory**:
   - Profile and optimize memory-intensive operations
   - Use generators and streaming where possible
   - Horizontal scaling for memory-bound scenarios

## Validation

### Success Criteria

- [ ] Complete Azure resource discovery module
- [ ] Achieve <500ms average API response time
- [ ] Handle 1000+ concurrent cloud API calls
- [ ] Maintain >90% test coverage
- [ ] Successfully onboard new developers within 1 week

### Review Date

This decision should be reviewed after:
1. Completing Phase 1 (Foundation) - ~2 months
2. If performance issues arise that can't be solved with optimization
3. If cloud SDKs become significantly better in another language

## References

- [Issue #1: Technology Stack Decision](../../issues/issue-001-technology-stack-decision.md)
- [Python POC](../../../docs/pocs/python-azure-discovery-poc.py)
- [Go POC](../../../docs/pocs/go-azure-discovery-poc.go)
- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

## Appendix: Alternative Considered

### Option 2: Go Stack
**Rejected**: While Go offers better raw performance, the benefits don't justify the tradeoffs in development velocity, SDK quality, and ecosystem richness for our I/O-bound use case.

### Option 3: Hybrid Approach
**Rejected**: Operational complexity and maintenance burden outweigh marginal performance gains. Single-language stack preferred for simplicity.

### Future Consideration: Rust
If we need extreme performance for specific components (e.g., graph algorithms), we can write Python extensions in Rust using PyO3. This gives us performance where needed without splitting the entire codebase.

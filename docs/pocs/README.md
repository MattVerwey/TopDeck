# Proof of Concept Implementations

This directory contains proof-of-concept (POC) implementations created during the technology evaluation phase.

## Contents

### Python Azure Discovery POC

**File**: `python-azure-discovery-poc.py`

A proof-of-concept implementation demonstrating Azure resource discovery using Python 3.11+ with async/await.

**Features**:
- Async/await pattern for concurrent discovery
- Simulates discovery of 6 Azure resource types (VMs, App Services, AKS, SQL, Storage, Load Balancers)
- Builds a simple dependency graph
- Clean, readable code with dataclasses

**Run**:
```bash
python3 python-azure-discovery-poc.py
```

**Key Takeaways**:
- ✅ Clean, concise syntax (~250 lines)
- ✅ Excellent async/await support
- ✅ Built-in dataclasses for resource modeling
- ✅ Easy to understand and maintain
- ⏱️ Performance: 0.10s for 6 concurrent discovery tasks

### Go Azure Discovery POC

**File**: `go-azure-discovery-poc.go`

A proof-of-concept implementation demonstrating Azure resource discovery using Go 1.24+ with goroutines.

**Features**:
- Goroutines and channels for concurrency
- Simulates discovery of 6 Azure resource types
- Builds a simple dependency graph
- Explicit error handling and type safety

**Run**:
```bash
go run go-azure-discovery-poc.go
```

**Key Takeaways**:
- ✅ Excellent concurrency primitives (goroutines, channels)
- ✅ Strong compile-time type checking
- ✅ Fast performance and low memory footprint
- ⚠️ More verbose (~350 lines for similar functionality)
- ⚠️ More boilerplate for error handling
- ⏱️ Performance: 0.10s for 6 concurrent discovery tasks

## Comparison Results

### Performance
Both implementations showed similar performance for I/O-bound operations (cloud API calls):
- **Python**: 0.10s
- **Go**: 0.10s

This confirmed that for network I/O-bound workloads (which is our primary use case), the performance difference is negligible.

### Code Quality
- **Python**: More concise (250 lines vs 350 lines)
- **Go**: More explicit error handling and type safety

### Developer Experience
- **Python**: Faster to write, easier to read, better cloud SDK support
- **Go**: Better compile-time safety, more tooling for large codebases

## Decision

Based on these POCs and additional research, **Python 3.11+ with FastAPI** was selected as the primary technology stack.

See [ADR-001: Technology Stack Selection](../architecture/adr/001-technology-stack.md) for the full decision rationale.

## Future POCs

Future proof-of-concepts that may be added to this directory:
- Neo4j graph operations performance
- FastAPI vs other Python web frameworks
- Frontend visualization libraries comparison
- Kubernetes deployment patterns

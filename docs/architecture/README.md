# TopDeck Architecture

This directory contains architectural documentation for the TopDeck platform.

## Contents

- [System Architecture](system-architecture.md) - High-level system design
- [Data Models](data-models.md) - Core data structures and relationships
- [Network Flow Diagrams](network-flow-diagrams.md) - Complete network topology and data flow patterns
- [Topology Examples](topology-examples.md) - Real-world topology examples
- [API Design](api-design.md) - REST API architecture
- [Security Model](security-model.md) - Authentication and authorization
- [Deployment Architecture](deployment-architecture.md) - Infrastructure setup

## Architecture Decision Records (ADRs)

ADRs document significant architectural decisions:

- [ADR-001: Technology Stack Selection](adr/001-technology-stack.md) - TBD
- [ADR-002: Graph Database Choice](adr/002-graph-database.md) - TBD
- [ADR-003: Multi-tenancy Design](adr/003-multi-tenancy.md) - TBD

## Key Architectural Principles

1. **Modularity** - Components should be loosely coupled and highly cohesive
2. **Scalability** - Design for horizontal scaling from the start
3. **Security First** - Security considerations in every design decision
4. **Cloud Native** - Leverage cloud services and patterns
5. **Observable** - Built-in logging, metrics, and tracing
6. **Resilient** - Handle failures gracefully

## Architecture Diagrams

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard (React)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / Load Balancer               │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Discovery  │  │ Integration │  │   Analysis  │
│   Service   │  │   Service   │  │   Service   │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                 │
       └────────────────┼─────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Neo4j     │  │    Redis    │  │  Message    │
│   Graph DB  │  │    Cache    │  │   Queue     │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Data Flow Diagram

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Azure   │     │   AWS    │     │   GCP    │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                 │
     └────────────────┼─────────────────┘
                      ▼
            ┌──────────────────┐
            │  Discovery Jobs  │
            └─────────┬────────┘
                      │
                      ▼
            ┌──────────────────┐
            │   Graph Builder  │
            └─────────┬────────┘
                      │
                      ▼
            ┌──────────────────┐
            │   Neo4j Storage  │
            └─────────┬────────┘
                      │
                      ▼
            ┌──────────────────┐
            │  Risk Analyzer   │
            └─────────┬────────┘
                      │
                      ▼
            ┌──────────────────┐
            │   Visualization  │
            └──────────────────┘
```

## Network Flow Visualization

For complete network flow diagrams showing how data flows from pods to load balancers, gateways, and storage accounts, see:
- **[Network Flow Diagrams](network-flow-diagrams.md)** - Comprehensive data flow patterns for Azure, AWS, and GCP

These diagrams illustrate:
- Pod-to-Load Balancer-to-Gateway-to-Storage flows
- Service mesh communication patterns
- Private endpoint and network security flows
- Multi-cloud network topologies
- Security and performance optimization patterns

These patterns form the foundation for TopDeck's network topology visualization dashboard (Issue #6).

## Next Steps

1. Implement interactive topology visualization (Issue #6)
2. Build risk analysis engine (Issue #5)
3. Add monitoring integration (Issue #7)
4. Complete AWS/GCP discoverer implementations
5. Create deployment automation tools

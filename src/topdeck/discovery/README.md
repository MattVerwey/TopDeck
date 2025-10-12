# TopDeck Discovery Module

This module provides cloud resource discovery functionality for TopDeck.

## Overview

The discovery module is responsible for:
- Discovering cloud resources across Azure, AWS, and GCP
- Mapping cloud-specific resource types to TopDeck's normalized model
- Detecting dependencies and relationships between resources
- Storing discovered resources in Neo4j graph database

## Architecture

```
discovery/
├── models.py              # Common data models (DiscoveredResource, ResourceDependency)
├── azure/                 # Azure-specific discovery
│   ├── __init__.py
│   ├── discoverer.py      # Main Azure discovery orchestrator
│   ├── mapper.py          # Azure → TopDeck resource mapping
│   └── resources.py       # Specialized resource discovery functions
├── aws/                   # AWS-specific discovery (TODO)
└── gcp/                   # GCP-specific discovery (TODO)

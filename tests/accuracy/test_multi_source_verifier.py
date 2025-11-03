"""
Tests for multi-source dependency verification.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from topdeck.analysis.accuracy.multi_source_verifier import (
    MultiSourceDependencyVerifier,
    VerificationEvidence,
)


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j client."""
    client = MagicMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
def mock_ado_discoverer():
    """Mock Azure DevOps discoverer."""
    return MagicMock()


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus collector."""
    collector = MagicMock()
    collector.query = AsyncMock(return_value=[])
    collector.query_range = AsyncMock(return_value=[])
    return collector


@pytest.fixture
def mock_tempo():
    """Mock Tempo collector."""
    collector = MagicMock()
    collector.search_traces = AsyncMock(return_value=[])
    return collector


@pytest.fixture
def verifier(mock_neo4j, mock_ado_discoverer, mock_prometheus, mock_tempo):
    """Create verifier with all mocks."""
    return MultiSourceDependencyVerifier(
        neo4j_client=mock_neo4j,
        ado_discoverer=mock_ado_discoverer,
        prometheus_collector=mock_prometheus,
        tempo_collector=mock_tempo,
    )


@pytest.mark.asyncio
async def test_verify_dependency_all_sources(verifier, mock_neo4j):
    """Test verification with evidence from all sources."""
    # Mock resource data
    mock_neo4j.execute_query.side_effect = [
        # First call: get source resource
        [
            {
                "id": "source-1",
                "name": "web-app",
                "type": "Microsoft.Web/sites",
                "properties": {"virtualNetwork": "vnet-1"},
                "ip_addresses": ["10.0.1.10"],
                "backend_pools": [
                    {"name": "backend-1", "ip_addresses": ["10.0.2.20"]}
                ],
                "endpoint": "https://web-app.azurewebsites.net",
            }
        ],
        # Second call: get target resource
        [
            {
                "id": "target-1",
                "name": "sql-db",
                "type": "Microsoft.Sql/servers/databases",
                "properties": {"virtualNetwork": "vnet-1"},
                "ip_addresses": ["10.0.2.20"],
                "backend_pools": [],
                "endpoint": "sql-server.database.windows.net",
            }
        ],
        # Third call: check VNet peering
        [{"exists": False}],
        # Fourth call: get ADO deployments
        [
            {
                "repository": "web-app-repo",
                "pipeline": "deploy-web",
                "config": {
                    "connectionString": "Server=sql-server.database.windows.net;Database=mydb"
                },
            }
        ],
    ]

    # Mock Prometheus data
    verifier.prometheus.query_range = AsyncMock(
        return_value=[
            {
                "values": [
                    [1234567890, "10.5"],
                    [1234567900, "12.3"],
                ]
            }
        ]
    )

    # Mock Tempo data
    mock_trace = MagicMock()
    mock_trace.trace_id = "trace-123"
    mock_trace.duration_ms = 150.0
    mock_trace.spans = [
        MagicMock(
            service_name="source-1",
            span_id="span-1",
            parent_span_id=None,
        ),
        MagicMock(
            service_name="target-1",
            span_id="span-2",
            parent_span_id="span-1",
        ),
    ]
    verifier.tempo.search_traces = AsyncMock(return_value=[mock_trace])

    # Execute verification
    result = await verifier.verify_dependency("source-1", "target-1")

    # Assertions
    assert result.source_id == "source-1"
    assert result.target_id == "target-1"
    assert result.is_verified
    assert len(result.evidence) == 4  # All sources provided evidence
    assert result.verification_score >= 0.6
    assert result.overall_confidence > 0.0

    # Check evidence sources
    evidence_sources = {ev.source for ev in result.evidence}
    assert "azure_infrastructure" in evidence_sources
    assert "ado_code" in evidence_sources
    assert "prometheus" in evidence_sources
    assert "tempo" in evidence_sources


@pytest.mark.asyncio
async def test_verify_dependency_azure_infrastructure_only(verifier, mock_neo4j):
    """Test verification with only Azure infrastructure evidence."""
    # Mock resource data with IP match
    mock_neo4j.execute_query.side_effect = [
        # Source resource
        [
            {
                "id": "lb-1",
                "name": "load-balancer",
                "type": "Microsoft.Network/loadBalancers",
                "properties": {},
                "ip_addresses": ["10.0.1.5"],
                "backend_pools": [
                    {"name": "backend-pool", "ip_addresses": ["10.0.2.10", "10.0.2.11"]}
                ],
                "endpoint": None,
            }
        ],
        # Target resource
        [
            {
                "id": "vm-1",
                "name": "web-vm",
                "type": "Microsoft.Compute/virtualMachines",
                "properties": {},
                "ip_addresses": ["10.0.2.10"],
                "backend_pools": [],
                "endpoint": None,
            }
        ],
        # VNet peering check
        [{"exists": False}],
        # ADO deployments (empty)
        [],
    ]

    # No Prometheus or Tempo data
    verifier.prometheus.query_range = AsyncMock(return_value=[])
    verifier.tempo.search_traces = AsyncMock(return_value=[])

    result = await verifier.verify_dependency("lb-1", "vm-1")

    assert result.source_id == "lb-1"
    assert result.target_id == "vm-1"
    assert len(result.evidence) == 1
    assert result.evidence[0].source == "azure_infrastructure"
    assert "Target IPs" in result.evidence[0].details["evidence_items"][0]
    assert result.evidence[0].confidence > 0.0


@pytest.mark.asyncio
async def test_verify_dependency_ado_code_only(verifier, mock_neo4j):
    """Test verification with only ADO code evidence."""
    mock_neo4j.execute_query.side_effect = [
        # Source resource
        [
            {
                "id": "app-1",
                "name": "api-service",
                "type": "Microsoft.Web/sites",
                "properties": {},
                "ip_addresses": [],
                "backend_pools": [],
                "endpoint": None,
            }
        ],
        # Target resource
        [
            {
                "id": "storage-1",
                "name": "storage-account",
                "type": "Microsoft.Storage/storageAccounts",
                "properties": {},
                "ip_addresses": [],
                "backend_pools": [],
                "endpoint": "storage-account.blob.core.windows.net",
            }
        ],
        # VNet peering check
        [{"exists": False}],
        # ADO deployments
        [
            {
                "repository": "api-repo",
                "pipeline": "deploy-api",
                "config": {
                    "storageAccountName": "storage-account",
                    "storageConnectionString": "DefaultEndpointsProtocol=https;AccountName=storage-account",
                },
            }
        ],
    ]

    # No monitoring data
    verifier.prometheus.query_range = AsyncMock(return_value=[])
    verifier.tempo.search_traces = AsyncMock(return_value=[])

    result = await verifier.verify_dependency("app-1", "storage-1")

    assert len(result.evidence) == 1
    assert result.evidence[0].source == "ado_code"
    assert any(
        "storage" in item.lower()
        for item in result.evidence[0].details["evidence_items"]
    )


@pytest.mark.asyncio
async def test_verify_dependency_monitoring_only(verifier, mock_neo4j):
    """Test verification with only monitoring data (Prometheus + Tempo)."""
    mock_neo4j.execute_query.side_effect = [
        # Source resource (no infra evidence)
        [
            {
                "id": "svc-1",
                "name": "frontend",
                "type": "service",
                "properties": {},
                "ip_addresses": [],
                "backend_pools": [],
                "endpoint": None,
            }
        ],
        # Target resource
        [
            {
                "id": "svc-2",
                "name": "backend-api",
                "type": "service",
                "properties": {},
                "ip_addresses": [],
                "backend_pools": [],
                "endpoint": None,
            }
        ],
        # VNet peering
        [{"exists": False}],
        # No ADO deployments
        [],
    ]

    # Mock Prometheus traffic
    verifier.prometheus.query_range = AsyncMock(
        return_value=[
            {
                "values": [
                    [1234567890, "100"],
                    [1234567900, "120"],
                ]
            }
        ]
    )

    # Mock Tempo traces
    mock_trace = MagicMock()
    mock_trace.trace_id = "trace-abc"
    mock_trace.duration_ms = 50.0
    mock_trace.spans = [
        MagicMock(service_name="svc-1", span_id="1", parent_span_id=None),
        MagicMock(service_name="svc-2", span_id="2", parent_span_id="1"),
    ]
    verifier.tempo.search_traces = AsyncMock(return_value=[mock_trace])

    result = await verifier.verify_dependency("svc-1", "svc-2")

    assert len(result.evidence) == 2  # Prometheus + Tempo
    evidence_sources = {ev.source for ev in result.evidence}
    assert "prometheus" in evidence_sources
    assert "tempo" in evidence_sources


@pytest.mark.asyncio
async def test_verify_dependency_no_evidence(verifier, mock_neo4j):
    """Test verification with no evidence from any source."""
    mock_neo4j.execute_query.side_effect = [
        # Source resource (minimal)
        [
            {
                "id": "res-1",
                "name": "resource-1",
                "type": "resource",
                "properties": {},
                "ip_addresses": [],
                "backend_pools": [],
                "endpoint": None,
            }
        ],
        # Target resource (minimal)
        [
            {
                "id": "res-2",
                "name": "resource-2",
                "type": "resource",
                "properties": {},
                "ip_addresses": [],
                "backend_pools": [],
                "endpoint": None,
            }
        ],
        # VNet peering
        [{"exists": False}],
        # No ADO deployments
        [],
    ]

    # No monitoring data
    verifier.prometheus.query_range = AsyncMock(return_value=[])
    verifier.tempo.search_traces = AsyncMock(return_value=[])

    result = await verifier.verify_dependency("res-1", "res-2")

    assert not result.is_verified
    assert result.verification_score == 0.0
    assert result.overall_confidence == 0.0
    assert len(result.evidence) == 0
    assert len(result.recommendations) > 0


@pytest.mark.asyncio
async def test_verify_dependency_resource_not_found(verifier, mock_neo4j):
    """Test verification when resource doesn't exist."""
    mock_neo4j.execute_query.return_value = []

    result = await verifier.verify_dependency("missing-1", "missing-2")

    assert not result.is_verified
    assert result.overall_confidence == 0.0
    assert "not found" in result.recommendations[0].lower()


def test_calculate_verification_score_all_sources(verifier):
    """Test verification score calculation with all sources."""
    evidence = [
        VerificationEvidence(
            source="azure_infrastructure",
            evidence_type="network",
            confidence=0.9,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
        VerificationEvidence(
            source="ado_code",
            evidence_type="config",
            confidence=0.8,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
        VerificationEvidence(
            source="prometheus",
            evidence_type="metrics",
            confidence=0.7,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
        VerificationEvidence(
            source="tempo",
            evidence_type="traces",
            confidence=0.85,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
    ]

    score = verifier._calculate_verification_score(evidence)

    assert score == 0.8125  # 4 sources = base score 1.0, adjusted by avg confidence (0.8125)


def test_calculate_verification_score_partial(verifier):
    """Test verification score with partial evidence."""
    evidence = [
        VerificationEvidence(
            source="azure_infrastructure",
            evidence_type="network",
            confidence=0.6,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
        VerificationEvidence(
            source="tempo",
            evidence_type="traces",
            confidence=0.7,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
    ]

    score = verifier._calculate_verification_score(evidence)

    assert 0.4 < score < 0.8  # 2 sources: base score is 0.70, but final score is base × avg confidence (can be as low as ~0.45)


def test_calculate_overall_confidence(verifier):
    """Test overall confidence calculation with weighted sources."""
    evidence = [
        VerificationEvidence(
            source="azure_infrastructure",
            evidence_type="network",
            confidence=1.0,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
        VerificationEvidence(
            source="prometheus",
            evidence_type="metrics",
            confidence=0.5,
            details={},
            verified_at=datetime.now(timezone.utc),
        ),
    ]

    confidence = verifier._calculate_overall_confidence(evidence)

    # azure_infrastructure (0.9 weight) * 1.0 + prometheus (0.75 weight) * 0.5
    # = 0.9 + 0.375 = 1.275 / 1.65 = 0.772...
    assert 0.75 < confidence < 0.80

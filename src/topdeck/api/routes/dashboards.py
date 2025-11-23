"""
API routes for custom dashboard management.

Provides CRUD operations for saving and loading custom monitoring dashboards
with configurable widgets and layouts.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboards"])

# Global service instances (in production, use dependency injection)
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


# Pydantic models for API


class WidgetPosition(BaseModel):
    """Widget position and size in grid layout."""
    
    x: int = Field(ge=0, description="X position in grid (column)")
    y: int = Field(ge=0, description="Y position in grid (row)")
    width: int = Field(ge=1, le=12, description="Widget width (1-12 columns)")
    height: int = Field(ge=1, description="Widget height in rows")


class WidgetConfig(BaseModel):
    """Widget configuration."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(description="Widget type (health_gauge, anomaly_timeline, etc.)")
    title: str = Field(description="Widget display title")
    position: WidgetPosition
    config: dict[str, Any] = Field(default_factory=dict, description="Widget-specific configuration")
    refresh_interval: int = Field(default=30, ge=10, description="Refresh interval in seconds")


class DashboardCreate(BaseModel):
    """Request model for creating a dashboard."""
    
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_default: bool = Field(default=False, description="Whether this is the default dashboard")
    widgets: list[WidgetConfig] = Field(default_factory=list)
    layout_config: dict[str, Any] = Field(default_factory=dict, description="Grid layout configuration")


class DashboardUpdate(BaseModel):
    """Request model for updating a dashboard."""
    
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_default: Optional[bool] = None
    widgets: Optional[list[WidgetConfig]] = None
    layout_config: Optional[dict[str, Any]] = None


class Dashboard(BaseModel):
    """Dashboard model."""
    
    id: str
    name: str
    description: Optional[str] = None
    is_default: bool = False
    owner: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    widgets: list[WidgetConfig]
    layout_config: dict[str, Any] = Field(default_factory=dict)


class DashboardTemplate(BaseModel):
    """Dashboard template for quick setup."""
    
    id: str
    name: str
    description: str
    category: str
    widgets: list[WidgetConfig]
    layout_config: dict[str, Any]


# API endpoints


@router.post("", response_model=Dashboard, status_code=201)
async def create_dashboard(
    dashboard: DashboardCreate,
    owner: str = Query(default="default", description="Dashboard owner ID"),
) -> Dashboard:
    """
    Create a new custom dashboard.
    
    Args:
        dashboard: Dashboard configuration
        owner: Owner user ID (in production, extract from auth token)
        
    Returns:
        Created dashboard with generated ID
    """
    try:
        neo4j = get_neo4j_client()
        
        dashboard_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        
        # Create dashboard node in Neo4j
        query = """
        CREATE (d:Dashboard {
            id: $id,
            name: $name,
            description: $description,
            is_default: $is_default,
            owner: $owner,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            widgets: $widgets,
            layout_config: $layout_config
        })
        RETURN d
        """
        
        # Convert widgets to JSON-serializable format
        widgets_data = [w.model_dump() for w in dashboard.widgets]
        
        result = neo4j.query(
            query,
            {
                "id": dashboard_id,
                "name": dashboard.name,
                "description": dashboard.description,
                "is_default": dashboard.is_default,
                "owner": owner,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "widgets": widgets_data,
                "layout_config": dashboard.layout_config,
            },
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create dashboard")
        
        logger.info(f"Created dashboard: {dashboard_id} for owner: {owner}")
        
        return Dashboard(
            id=dashboard_id,
            name=dashboard.name,
            description=dashboard.description,
            is_default=dashboard.is_default,
            owner=owner,
            created_at=now,
            updated_at=now,
            widgets=dashboard.widgets,
            layout_config=dashboard.layout_config,
        )
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[Dashboard])
async def list_dashboards(
    owner: str = Query(default="default", description="Filter by owner ID"),
    include_defaults: bool = Query(default=True, description="Include default dashboards"),
) -> list[Dashboard]:
    """
    List all dashboards for a user.
    
    Args:
        owner: Owner user ID to filter by
        include_defaults: Whether to include default/template dashboards
        
    Returns:
        List of dashboards
    """
    try:
        neo4j = get_neo4j_client()
        
        # Build query based on filters
        if include_defaults:
            query = """
            MATCH (d:Dashboard)
            WHERE d.owner = $owner OR d.is_default = true
            RETURN d
            ORDER BY d.is_default DESC, d.updated_at DESC
            """
        else:
            query = """
            MATCH (d:Dashboard {owner: $owner})
            RETURN d
            ORDER BY d.updated_at DESC
            """
        
        results = neo4j.query(query, {"owner": owner})
        
        dashboards = []
        for record in results:
            node = record["d"]
            dashboards.append(Dashboard(
                id=node["id"],
                name=node["name"],
                description=node.get("description"),
                is_default=node.get("is_default", False),
                owner=node.get("owner"),
                created_at=datetime.fromisoformat(node["created_at"]),
                updated_at=datetime.fromisoformat(node["updated_at"]),
                widgets=[WidgetConfig(**w) for w in node.get("widgets", [])],
                layout_config=node.get("layout_config", {}),
            ))
        
        logger.info(f"Found {len(dashboards)} dashboards for owner: {owner}")
        return dashboards
        
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(dashboard_id: str) -> Dashboard:
    """
    Get a specific dashboard by ID.
    
    Args:
        dashboard_id: Dashboard ID
        
    Returns:
        Dashboard details
    """
    try:
        neo4j = get_neo4j_client()
        
        query = """
        MATCH (d:Dashboard {id: $id})
        RETURN d
        """
        
        results = neo4j.query(query, {"id": dashboard_id})
        
        if not results:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        node = results[0]["d"]
        
        return Dashboard(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            is_default=node.get("is_default", False),
            owner=node.get("owner"),
            created_at=datetime.fromisoformat(node["created_at"]),
            updated_at=datetime.fromisoformat(node["updated_at"]),
            widgets=[WidgetConfig(**w) for w in node.get("widgets", [])],
            layout_config=node.get("layout_config", {}),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{dashboard_id}", response_model=Dashboard)
async def update_dashboard(
    dashboard_id: str,
    update: DashboardUpdate,
) -> Dashboard:
    """
    Update an existing dashboard.
    
    Args:
        dashboard_id: Dashboard ID to update
        update: Updated dashboard fields
        
    Returns:
        Updated dashboard
    """
    try:
        neo4j = get_neo4j_client()
        
        # First check if dashboard exists
        check_query = "MATCH (d:Dashboard {id: $id}) RETURN d"
        check_results = neo4j.query(check_query, {"id": dashboard_id})
        
        if not check_results:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Build update query dynamically based on provided fields
        set_clauses = ["d.updated_at = datetime($updated_at)"]
        params: dict[str, Any] = {
            "id": dashboard_id,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        
        if update.name is not None:
            set_clauses.append("d.name = $name")
            params["name"] = update.name
        
        if update.description is not None:
            set_clauses.append("d.description = $description")
            params["description"] = update.description
        
        if update.is_default is not None:
            set_clauses.append("d.is_default = $is_default")
            params["is_default"] = update.is_default
        
        if update.widgets is not None:
            set_clauses.append("d.widgets = $widgets")
            params["widgets"] = [w.model_dump() for w in update.widgets]
        
        if update.layout_config is not None:
            set_clauses.append("d.layout_config = $layout_config")
            params["layout_config"] = update.layout_config
        
        query = f"""
        MATCH (d:Dashboard {{id: $id}})
        SET {', '.join(set_clauses)}
        RETURN d
        """
        
        results = neo4j.query(query, params)
        
        if not results:
            raise HTTPException(status_code=500, detail="Failed to update dashboard")
        
        node = results[0]["d"]
        
        logger.info(f"Updated dashboard: {dashboard_id}")
        
        return Dashboard(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            is_default=node.get("is_default", False),
            owner=node.get("owner"),
            created_at=datetime.fromisoformat(node["created_at"]),
            updated_at=datetime.fromisoformat(node["updated_at"]),
            widgets=[WidgetConfig(**w) for w in node.get("widgets", [])],
            layout_config=node.get("layout_config", {}),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(dashboard_id: str) -> None:
    """
    Delete a dashboard.
    
    Args:
        dashboard_id: Dashboard ID to delete
    """
    try:
        neo4j = get_neo4j_client()
        
        query = """
        MATCH (d:Dashboard {id: $id})
        DELETE d
        RETURN count(d) as deleted_count
        """
        
        results = neo4j.query(query, {"id": dashboard_id})
        
        if not results or results[0]["deleted_count"] == 0:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        logger.info(f"Deleted dashboard: {dashboard_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/list", response_model=list[DashboardTemplate])
async def list_dashboard_templates() -> list[DashboardTemplate]:
    """
    Get available dashboard templates.
    
    Returns:
        List of pre-configured dashboard templates
    """
    # Define default templates
    templates = [
        DashboardTemplate(
            id="overview",
            name="System Overview",
            description="High-level view of system health and performance",
            category="monitoring",
            widgets=[
                WidgetConfig(
                    type="health_gauge",
                    title="Overall Health Score",
                    position=WidgetPosition(x=0, y=0, width=4, height=2),
                    config={"show_trend": True},
                ),
                WidgetConfig(
                    type="top_failing_services",
                    title="Top 5 Failing Services",
                    position=WidgetPosition(x=4, y=0, width=4, height=2),
                    config={"limit": 5},
                ),
                WidgetConfig(
                    type="anomaly_timeline",
                    title="Recent Anomalies",
                    position=WidgetPosition(x=8, y=0, width=4, height=2),
                    config={"hours": 24},
                ),
                WidgetConfig(
                    type="traffic_heatmap",
                    title="Service Traffic Heatmap",
                    position=WidgetPosition(x=0, y=2, width=12, height=3),
                    config={"show_errors": True},
                ),
            ],
            layout_config={"cols": 12, "rowHeight": 80, "margin": [10, 10]},
        ),
        DashboardTemplate(
            id="performance",
            name="Performance Monitoring",
            description="Focus on latency, throughput, and resource utilization",
            category="performance",
            widgets=[
                WidgetConfig(
                    type="custom_metric",
                    title="P95 Latency",
                    position=WidgetPosition(x=0, y=0, width=6, height=2),
                    config={"metric": "latency_p95", "chart_type": "line"},
                ),
                WidgetConfig(
                    type="custom_metric",
                    title="Request Rate",
                    position=WidgetPosition(x=6, y=0, width=6, height=2),
                    config={"metric": "request_rate", "chart_type": "area"},
                ),
                WidgetConfig(
                    type="custom_metric",
                    title="CPU Utilization",
                    position=WidgetPosition(x=0, y=2, width=6, height=2),
                    config={"metric": "cpu_usage", "chart_type": "line"},
                ),
                WidgetConfig(
                    type="custom_metric",
                    title="Memory Usage",
                    position=WidgetPosition(x=6, y=2, width=6, height=2),
                    config={"metric": "memory_usage", "chart_type": "line"},
                ),
            ],
            layout_config={"cols": 12, "rowHeight": 80, "margin": [10, 10]},
        ),
        DashboardTemplate(
            id="error_tracking",
            name="Error Tracking",
            description="Monitor errors, anomalies, and service failures",
            category="reliability",
            widgets=[
                WidgetConfig(
                    type="anomaly_timeline",
                    title="Anomaly Timeline (24h)",
                    position=WidgetPosition(x=0, y=0, width=12, height=2),
                    config={"hours": 24, "severity_filter": "all"},
                ),
                WidgetConfig(
                    type="top_failing_services",
                    title="Services with Most Errors",
                    position=WidgetPosition(x=0, y=2, width=6, height=3),
                    config={"limit": 10, "sort_by": "error_count"},
                ),
                WidgetConfig(
                    type="custom_metric",
                    title="Error Rate Trends",
                    position=WidgetPosition(x=6, y=2, width=6, height=3),
                    config={"metric": "error_rate", "chart_type": "line"},
                ),
            ],
            layout_config={"cols": 12, "rowHeight": 80, "margin": [10, 10]},
        ),
    ]
    
    return templates


@router.post("/templates/{template_id}/create", response_model=Dashboard, status_code=201)
async def create_dashboard_from_template(
    template_id: str,
    owner: str = Query(default="default", description="Dashboard owner ID"),
) -> Dashboard:
    """
    Create a new dashboard from a template.
    
    Args:
        template_id: Template ID to use
        owner: Owner user ID
        
    Returns:
        Created dashboard
    """
    try:
        # Get template
        templates = await list_dashboard_templates()
        template = next((t for t in templates if t.id == template_id), None)
        
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create dashboard from template
        dashboard_create = DashboardCreate(
            name=f"{template.name} (Custom)",
            description=template.description,
            is_default=False,
            widgets=template.widgets,
            layout_config=template.layout_config,
        )
        
        return await create_dashboard(dashboard_create, owner)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dashboard from template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

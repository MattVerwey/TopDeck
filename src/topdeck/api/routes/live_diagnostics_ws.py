"""
Live Diagnostics WebSocket endpoint.

Provides real-time updates for diagnostics data via WebSocket connection.
Clients receive instant notifications when:
- Service health status changes
- New anomalies are detected
- Traffic patterns become abnormal
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from topdeck.analysis.prediction.feature_extractor import FeatureExtractor
from topdeck.analysis.prediction.predictor import Predictor
from topdeck.common.config import settings
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.live_diagnostics import LiveDiagnosticsService
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["live-diagnostics-websocket"])


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates to clients."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            conn_count = len(self.active_connections)
        logger.info(
            "WebSocket connected",
            extra={
                "client": websocket.client,
                "total_connections": conn_count,
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            conn_count = len(self.active_connections)
        logger.info(
            "WebSocket disconnected",
            extra={
                "client": websocket.client,
                "total_connections": conn_count,
            },
        )

    async def has_connections(self) -> bool:
        """Check if there are any active connections (thread-safe)."""
        async with self._lock:
            return len(self.active_connections) > 0

    async def get_connection_count(self) -> int:
        """Get the number of active connections (thread-safe)."""
        async with self._lock:
            return len(self.active_connections)

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(
                        "Failed to send message to client",
                        extra={"error": str(e), "client": connection.client},
                    )
                    disconnected.append(connection)

            # Remove failed connections
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(
                "Failed to send personal message",
                extra={"error": str(e), "client": websocket.client},
            )


# Global connection manager instance
manager = ConnectionManager()


class DiagnosticsUpdatePublisher:
    """Publishes diagnostic updates to WebSocket clients."""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self._running = False
        self._task: asyncio.Task | None = None
        # Initialize service instances once for reuse
        self._neo4j_client: Neo4jClient | None = None
        self._prometheus: PrometheusCollector | None = None
        self._predictor: Predictor | None = None
        self._service: LiveDiagnosticsService | None = None

    def _initialize_services(self):
        """Initialize service instances for reuse."""
        if self._service is None:
            self._neo4j_client = Neo4jClient(
                uri=settings.neo4j_uri,
                username=settings.neo4j_username,
                password=settings.neo4j_password,
            )
            self._prometheus = PrometheusCollector(settings.prometheus_url)
            self._predictor = Predictor()
            self._service = LiveDiagnosticsService(
                prometheus_collector=self._prometheus,
                neo4j_client=self._neo4j_client,
                predictor=self._predictor,
            )

    async def _cleanup_services(self):
        """Clean up service instances."""
        if self._prometheus and hasattr(self._prometheus, 'close'):
            await self._prometheus.close()
        if self._neo4j_client:
            self._neo4j_client.close()
        self._neo4j_client = None
        self._prometheus = None
        self._predictor = None
        self._service = None

    def is_running(self) -> bool:
        """Check if publisher is currently running."""
        return self._running

    async def start(self, update_interval: int = 10):
        """Start publishing updates at regular intervals."""
        if self._running:
            logger.warning("Publisher already running")
            return

        self._running = True
        self._initialize_services()
        self._task = asyncio.create_task(self._publish_loop(update_interval))
        logger.info(
            "Started diagnostics update publisher",
            extra={"update_interval": update_interval},
        )

    async def stop(self):
        """Stop publishing updates."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                # Task cancellation is expected when stopping the publisher; ignore this exception.
                pass
        self._cleanup_services()
        logger.info("Stopped diagnostics update publisher")

    async def _publish_loop(self, interval: int):
        """Continuous loop that publishes updates."""
        while self._running:
            try:
                # Only publish if there are active connections
                if await self.manager.has_connections():
                    await self._publish_update()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in publish loop",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                await asyncio.sleep(interval)

    async def _publish_update(self):
        """Fetch and publish diagnostic updates."""
        try:
            # Use initialized service instances
            if self._service is None:
                self._initialize_services()

            # Get snapshot data
            snapshot = self._service.get_diagnostics_snapshot(duration_hours=1)

            # Convert to dict for JSON serialization
            message = {
                "type": "snapshot_update",
                "timestamp": datetime.now(UTC).isoformat(),
                "data": {
                    "services": [
                        {
                            "resource_id": s.resource_id,
                            "resource_name": s.resource_name,
                            "resource_type": s.resource_type,
                            "status": s.status,
                            "health_score": s.health_score,
                            "anomalies": s.anomalies,
                            "metrics": s.metrics,
                            "last_updated": s.last_updated.isoformat(),
                        }
                        for s in snapshot.services
                    ],
                    "anomalies": [
                        {
                            "alert_id": a.alert_id,
                            "resource_id": a.resource_id,
                            "resource_name": a.resource_name,
                            "severity": a.severity,
                            "metric_name": a.metric_name,
                            "current_value": a.current_value,
                            "expected_value": a.expected_value,
                            "deviation_percentage": a.deviation_percentage,
                            "timestamp": a.timestamp.isoformat(),
                            "description": a.description,
                        }
                        for a in snapshot.anomalies
                    ],
                    "traffic_patterns": [
                        {
                            "source_id": t.source_id,
                            "target_id": t.target_id,
                            "request_rate": t.request_rate,
                            "error_rate": t.error_rate,
                            "avg_latency_ms": t.avg_latency_ms,
                            "is_abnormal": t.is_abnormal,
                            "last_updated": t.last_updated.isoformat(),
                        }
                        for t in snapshot.traffic_patterns
                    ],
                    "failing_dependencies": [
                        {
                            "resource_id": f.resource_id,
                            "resource_name": f.resource_name,
                            "dependency_id": f.dependency_id,
                            "dependency_name": f.dependency_name,
                            "status": f.status,
                            "error_message": f.error_message,
                            "last_error_time": f.last_error_time.isoformat() if f.last_error_time else None,
                        }
                        for f in snapshot.failing_dependencies
                    ],
                    "overall_health": snapshot.overall_health,
                    "timestamp": snapshot.timestamp.isoformat(),
                },
            }

            await self.manager.broadcast(message)

        except Exception as e:
            logger.error(
                "Failed to publish diagnostics update",
                extra={"error": str(e)},
                exc_info=True,
            )

    async def publish_health_change(
        self, resource_id: str, old_status: str, new_status: str, health_score: float
    ):
        """Publish a service health change event."""
        message = {
            "type": "health_change",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {
                "resource_id": resource_id,
                "old_status": old_status,
                "new_status": new_status,
                "health_score": health_score,
            },
        }
        await self.manager.broadcast(message)

    async def publish_anomaly_detected(
        self, resource_id: str, metric_name: str, severity: str, description: str
    ):
        """Publish a new anomaly detection event."""
        message = {
            "type": "anomaly_detected",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {
                "resource_id": resource_id,
                "metric_name": metric_name,
                "severity": severity,
                "description": description,
            },
        }
        await self.manager.broadcast(message)

    async def publish_traffic_anomaly(
        self, source_id: str, target_id: str, anomaly_type: str, description: str
    ):
        """Publish a traffic pattern anomaly event."""
        message = {
            "type": "traffic_anomaly",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {
                "source_id": source_id,
                "target_id": target_id,
                "anomaly_type": anomaly_type,
                "description": description,
            },
        }
        await self.manager.broadcast(message)

    async def request_snapshot(self):
        """Request an immediate snapshot update (public method)."""
        await self._publish_update()


# Global publisher instance
publisher = DiagnosticsUpdatePublisher(manager)


@router.websocket("/live-diagnostics")
async def websocket_live_diagnostics(
    websocket: WebSocket,
    update_interval: int = Query(default=10, ge=1, le=60, description="Update interval in seconds"),
):
    """
    WebSocket endpoint for real-time diagnostics updates.
    
    Args:
        websocket: WebSocket connection
        update_interval: How often to send updates (1-60 seconds)
    
    Message Types Sent:
        - snapshot_update: Complete diagnostics snapshot
        - health_change: Service health status changed
        - anomaly_detected: New anomaly detected
        - traffic_anomaly: Traffic pattern anomaly detected
        - ping: Keep-alive ping
        - error: Error message
    
    Message Types Received:
        - subscribe: Subscribe to specific resources
        - unsubscribe: Unsubscribe from resources
        - get_snapshot: Request immediate snapshot
        - ping: Client ping (respond with pong)
    
    Example:
        ws://localhost:8000/api/v1/ws/live-diagnostics?update_interval=10
    """
    await manager.connect(websocket)
    
    try:
        # Start publisher if not already running (using public method)
        if not publisher.is_running():
            await publisher.start(update_interval)
        
        # Send initial welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "timestamp": datetime.now(UTC).isoformat(),
                "message": "Connected to live diagnostics WebSocket",
                "update_interval": update_interval,
            },
            websocket,
        )
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        {
                            "type": "pong",
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                        websocket,
                    )
                
                elif message_type == "get_snapshot":
                    # Send immediate snapshot using public method
                    await publisher.request_snapshot()
                
                elif message_type == "subscribe":
                    # Future: Implement resource-specific subscriptions
                    resource_ids = message.get("resource_ids", [])
                    logger.info(
                        "Client subscribed to resources",
                        extra={"resource_ids": resource_ids},
                    )
                    await manager.send_personal_message(
                        {
                            "type": "subscribed",
                            "timestamp": datetime.now(UTC).isoformat(),
                            "resource_ids": resource_ids,
                        },
                        websocket,
                    )
                
                elif message_type == "unsubscribe":
                    # Future: Implement resource-specific unsubscriptions
                    resource_ids = message.get("resource_ids", [])
                    logger.info(
                        "Client unsubscribed from resources",
                        extra={"resource_ids": resource_ids},
                    )
                    await manager.send_personal_message(
                        {
                            "type": "unsubscribed",
                            "timestamp": datetime.now(UTC).isoformat(),
                            "resource_ids": resource_ids,
                        },
                        websocket,
                    )
                
                else:
                    logger.warning(
                        "Unknown message type",
                        extra={"type": message_type},
                    )
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "timestamp": datetime.now(UTC).isoformat(),
                            "message": f"Unknown message type: {message_type}",
                        },
                        websocket,
                    )
            
            except json.JSONDecodeError as e:
                logger.warning(
                    "Invalid JSON received",
                    extra={"error": str(e)},
                )
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "message": "Invalid JSON format",
                    },
                    websocket,
                )
            
            except WebSocketDisconnect:
                raise
            
            except Exception as e:
                logger.error(
                    "Error handling message",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "message": str(e),
                    },
                    websocket,
                )
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    
    finally:
        await manager.disconnect(websocket)


@router.get("/live-diagnostics/health")
async def websocket_health():
    """
    Health check endpoint for WebSocket service.
    
    Returns:
        Status and number of active connections
    """
    return {
        "status": "healthy",
        "active_connections": await manager.get_connection_count(),
        "publisher_running": publisher.is_running(),
        "timestamp": datetime.now(UTC).isoformat(),
    }

"""
SanTrapik Real-Time Telemetry Streaming & Geospatial Pub/Sub Service
Manages Server-Sent Events (SSE) connections, client spatial viewport subscriptions,
and metric route corridor buffer chokepoint monitoring (< 100m alert radius).
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, AsyncGenerator
from fastapi import Request
from shapely.geometry import Point, LineString

logger = logging.getLogger("santrapik.streaming")

# Metric conversion constants at Metro Manila latitude (~14.5 N)
METERS_PER_DEG_LAT = 110600.0
METERS_PER_DEG_LNG = 107500.0

@dataclass
class ClientSubscriber:
    client_id: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    bbox: Optional[Tuple[float, float, float, float]] = None  # min_lng, min_lat, max_lng, max_lat
    route_id: Optional[str] = None
    route_coords: Optional[List[List[float]]] = None
    metric_line: Optional[LineString] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class TelemetryStreamManager:
    def __init__(self):
        self._subscribers: Dict[str, ClientSubscriber] = {}
        self._route_cache: Dict[str, List[List[float]]] = {}
        self._lock = asyncio.Lock()

    def register_route(self, route_id: str, coordinates: List[List[float]]) -> None:
        """Caches route coordinates for route buffer matching."""
        if not coordinates or len(coordinates) < 2:
            return
        self._route_cache[route_id] = coordinates

        # Update any active subscriber currently tuned to this route
        for sub in self._subscribers.values():
            if sub.route_id == route_id:
                self._attach_route_geometry(sub, coordinates)

    def _attach_route_geometry(self, subscriber: ClientSubscriber, coords: List[List[float]]) -> None:
        """Converts geographic line into projected metric LineString for fast distance queries."""
        try:
            metric_pts = [(pt[0] * METERS_PER_DEG_LNG, pt[1] * METERS_PER_DEG_LAT) for pt in coords]
            subscriber.route_coords = coords
            subscriber.metric_line = LineString(metric_pts)
        except Exception as err:
            logger.warning(f"Failed to build metric LineString for route: {err}")
            subscriber.metric_line = None

    async def register_subscriber(
        self,
        client_id: Optional[str] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        route_id: Optional[str] = None
    ) -> ClientSubscriber:
        """Registers an incoming SSE client connection."""
        c_id = client_id or f"client_{uuid.uuid4().hex[:10]}"
        subscriber = ClientSubscriber(
            client_id=c_id,
            bbox=bbox,
            route_id=route_id
        )

        if route_id and route_id in self._route_cache:
            self._attach_route_geometry(subscriber, self._route_cache[route_id])

        async with self._lock:
            self._subscribers[c_id] = subscriber

        logger.info(f"SSE subscriber registered: {c_id} (bbox={bbox}, route_id={route_id})")
        return subscriber

    async def update_subscriber_subscription(
        self,
        client_id: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        route_id: Optional[str] = None
    ) -> bool:
        """Dynamically updates client viewport and active route without dropping connection."""
        async with self._lock:
            sub = self._subscribers.get(client_id)
            if not sub:
                return False

            if bbox is not None:
                sub.bbox = bbox

            if route_id is not None:
                sub.route_id = route_id
                if route_id in self._route_cache:
                    self._attach_route_geometry(sub, self._route_cache[route_id])
                else:
                    sub.route_coords = None
                    sub.metric_line = None

            return True

    async def deregister_subscriber(self, client_id: str) -> None:
        """Removes a subscriber on client disconnect to prevent coroutine or memory leaks."""
        async with self._lock:
            if client_id in self._subscribers:
                del self._subscribers[client_id]
                logger.info(f"SSE subscriber deregistered: {client_id}")

    @property
    def active_subscriber_count(self) -> int:
        return len(self._subscribers)

    def is_point_in_bbox(self, lng: float, lat: float, bbox: Tuple[float, float, float, float]) -> bool:
        """Checks if a point falls within the subscriber's visible viewport."""
        min_lng, min_lat, max_lng, max_lat = bbox
        return (min_lng <= lng <= max_lng) and (min_lat <= lat <= max_lat)

    def calculate_route_distance_meters(self, lng: float, lat: float, subscriber: ClientSubscriber) -> Optional[float]:
        """Calculates distance in meters from point to subscriber's active route line."""
        if not subscriber.metric_line:
            return None
        pt_metric = Point(lng * METERS_PER_DEG_LNG, lat * METERS_PER_DEG_LAT)
        return float(subscriber.metric_line.distance(pt_metric))

    async def broadcast_incident(self, incident: Dict[str, Any]) -> int:
        """
        Broadcasting hub for incidents:
        1. Viewport filter: sends 'incident_update' only to subscribers whose bbox covers the point.
        2. Corridor buffer: if incident is within 100m of subscriber's active route, sends 'route_obstruction'.
        """
        lat = incident.get("lat")
        lng = incident.get("lng")
        if lat is None or lng is None:
            coords = incident.get("point_lng_lat", [None, None])
            lng, lat = coords[0], coords[1]

        if lat is None or lng is None:
            return 0

        dispatched = 0
        severity = str(incident.get("severity", "MEDIUM")).upper()
        delay_map = {"CRITICAL": 20, "HIGH": 12, "MEDIUM": 7, "LOW": 3}
        estimated_delay = delay_map.get(severity, 8)

        async with self._lock:
            subscribers_snapshot = list(self._subscribers.values())

        for sub in subscribers_snapshot:
            try:
                # 1. Route corridor buffer check (100m alert radius)
                if sub.metric_line:
                    dist_m = self.calculate_route_distance_meters(lng, lat, sub)
                    if dist_m is not None and dist_m <= 100.0:
                        route_alert = {
                            "event": "route_obstruction",
                            "data": {
                                "route_id": sub.route_id,
                                "incident_id": incident.get("id"),
                                "incident_type": incident.get("incident_type", "ACCIDENT"),
                                "severity": severity,
                                "corridor": incident.get("corridor", "Active Corridor"),
                                "description": incident.get("description", "Active obstruction directly along corridor"),
                                "distance_to_route_meters": round(dist_m, 1),
                                "estimated_delay_minutes": estimated_delay,
                                "recommendation": f"Hazard detected on route ({incident.get('corridor', 'Corridor')}). Recommend evaluating alternate path.",
                                "can_reroute": True,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }
                        await sub.queue.put(route_alert)
                        dispatched += 1

                # 2. General viewport check
                should_deliver = True
                if sub.bbox:
                    should_deliver = self.is_point_in_bbox(lng, lat, sub.bbox)

                if should_deliver:
                    await sub.queue.put({
                        "event": "incident_update",
                        "data": incident
                    })
                    dispatched += 1

            except Exception as err:
                logger.error(f"Error dispatching incident to subscriber {sub.client_id}: {err}")

        return dispatched

    async def broadcast_velocity_deltas(self, deltas: List[Dict[str, Any]]) -> int:
        """Broadcasts speed shifts to all connected clients."""
        if not deltas:
            return 0

        packet = {
            "event": "velocity_shift",
            "data": {
                "deltas": deltas,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        async with self._lock:
            subscribers_snapshot = list(self._subscribers.values())

        for sub in subscribers_snapshot:
            try:
                await sub.queue.put(packet)
            except Exception:
                continue

        return len(subscribers_snapshot)

    async def broadcast_stats(self, stats: Dict[str, Any]) -> int:
        """Broadcasts aggregate city dashboard statistics."""
        packet = {
            "event": "stats_update",
            "data": stats
        }

        async with self._lock:
            subscribers_snapshot = list(self._subscribers.values())

        for sub in subscribers_snapshot:
            try:
                await sub.queue.put(packet)
            except Exception:
                continue

        return len(subscribers_snapshot)

    async def stream_events(self, subscriber: ClientSubscriber, request: Request) -> AsyncGenerator[str, None]:
        """
        SSE event generator producing HTTP/2 compatible text/event-stream packets.
        Sends an immediate connection handshake, followed by queued events, and
        emits automated 15-second keepalive comments (: keepalive\n\n) to prevent NAT timeouts.
        """
        try:
            # 1. Connection established handshake
            handshake = {
                "client_id": subscriber.client_id,
                "keepalive_sec": 15,
                "connected_at": subscriber.created_at.isoformat(),
                "route_subscribed": subscriber.route_id
            }
            yield f"event: connection_established\ndata: {json.dumps(handshake)}\n\n"

            # 2. Stream loop with 15s keepalive
            while True:
                if await request.is_disconnected():
                    break

                try:
                    event_packet = await asyncio.wait_for(subscriber.queue.get(), timeout=15.0)
                    evt_type = event_packet.get("event", "message")
                    evt_data = json.dumps(event_packet.get("data", {}))
                    yield f"event: {evt_type}\ndata: {evt_data}\n\n"
                except asyncio.TimeoutError:
                    # 15s keepalive heartbeat ping
                    yield ": keepalive\n\n"

        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            await self.deregister_subscriber(subscriber.client_id)

stream_manager = TelemetryStreamManager()

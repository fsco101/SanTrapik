---
name: incident-telemetry-resilience
description: Use when implementing, reviewing, or securing real-time incident ingestion, crowdsourced report verification, anti-tampering defenses, spatiotemporal clustering, and live event broadcasting
---

# Incident Telemetry Resilience & Trust Architecture

## Overview
SanTrapik operates an **anonymous public-first access model** (no user logins, passwords, or OAuth). While this eliminates onboarding friction for commuters, it creates significant attack vectors: fake incident injections (e.g. reporting phantom road closures), griefing (maliciously resolving legitimate hazards), coordinate spoofing, and API denial-of-service.

This skill defines the defense-in-depth architecture, spatiotemporal clustering algorithms, incident lifecycle state machine, and viewport-filtered streaming protocols necessary to secure an open traffic intelligence system.

---

## 1. Threat Model & Commuter Incident Taxonomy

| Threat | Attack Vector | Mitigation in SanTrapik |
| :--- | :--- | :--- |
| **Phantom Incident Flooding** | Bot sends automated POST requests reporting fake accidents across major arteries. | Sliding-window IP rate limiting, client device fingerprinting, and spatiotemporal clustering requiring multi-report quorum. |
| **Malicious Incident Clearing** | Attacker calls `PATCH /incidents/{id}/resolve` to clear active road hazard warnings. | Cryptographic report session secret token requirement + multi-commuter confirmation voting ("Is this road cleared?"). |
| **PostGIS Spatial DoS** | Client submits complex concave bounding boxes or coordinates outside the country to force unindexed queries. | Hard-coded strict coordinate bounds validation (`METRO_MANILA_STRICT_BBOX`) and query timeout limits (`SET statement_timeout = '2000ms'`). |
| **XSS / HTML Injection** | Attacker injects `<script>` payloads into the incident `description` field. | Strict Pydantic v2 string sanitization, Bleach HTML stripping, and regex character constraints. |

### Commuter & Pedestrian Incident Categories
Commuters encounter hazards distinct from car drivers. The ingestion schema must accept and validate:
- `PEDESTRIAN_OBSTRUCTION`: Sidewalk blocked by illegal parking, vendors, or construction debris.
- `FLOODED_SIDEWALK`: Gutter-deep ($>0.15\text{m}$) or knee-deep ($>0.30\text{m}$) floodwaters making walking path impassable.
- `BROKEN_FOOTBRIDGE`: Damaged or closed pedestrian overpass requiring ground crossing.
- `TERMINAL_OVERCROWDING`: Massive commuter queues spilling into roadways at transit hubs (e.g. EDSA Carousel stations).
- `TRANSIT_DISRUPTION`: Stalled busway carrier, MRT/LRT track pause, or PUV strike causing sudden commuter corridor gridlock.

---

## 2. Spatiotemporal Clustering & Consensus Engine

Single anonymous reports must NEVER immediately become high-severity confirmed alerts. Instead, reports undergo spatiotemporal clustering (DBSCAN / proximity window) before elevation.

### Proximity & Time Quorum Rules
- **Spatial Radius**:
  - Vehicular corridors: $150\text{ meters}$
  - Pedestrian walking paths / stations: $80\text{ meters}$ (tighter threshold for localized sidewalk hazards)
- **Temporal Window**: $15\text{ minutes}$
- **Corroboration Quorum**:
  - `1 Report`: Status = `REPORTED`, Confidence = $0.35$ (Rendered with dashed outline and `[UNVERIFIED]` badge).
  - `2 Independent Reports`: Status = `VERIFIED`, Confidence = $0.75$ (Rendered with solid pulse).
  - `3+ Reports or Official Feed (MMDA/TomTom)`: Status = `VERIFIED`, Confidence = $0.95$.

```python
# backend/app/services/incident_consensus.py
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from shapely.geometry import Point

class IncidentConsensusEngine:
    SPATIAL_CLUSTER_METERS = 150.0
    PEDESTRIAN_CLUSTER_METERS = 80.0
    TEMPORAL_WINDOW_MINUTES = 15.0

    @classmethod
    def evaluate_incoming_report(
        cls, 
        new_report: Dict[str, Any], 
        active_incidents: List[Dict[str, Any]], 
        client_fingerprint: str
    ) -> Dict[str, Any]:
        """
        Matches an incoming report against active incidents to prevent duplicates
        and increment consensus confidence.
        """
        pt_new = Point(new_report["lng"], new_report["lat"])
        now = datetime.now(timezone.utc)
        is_pedestrian_report = new_report.get("incident_type") in [
            "PEDESTRIAN_OBSTRUCTION", "FLOODED_SIDEWALK", "BROKEN_FOOTBRIDGE"
        ]
        threshold_meters = cls.PEDESTRIAN_CLUSTER_METERS if is_pedestrian_report else cls.SPATIAL_CLUSTER_METERS

        for incident in active_incidents:
            if incident.get("status") == "RESOLVED":
                continue

            pt_existing = Point(incident["lng"], incident["lat"])
            # Approx metric distance at Manila latitude (1 deg lat ~ 110.6 km, 1 deg lng ~ 107.5 km)
            d_lat = (pt_new.y - pt_existing.y) * 110600.0
            d_lng = (pt_new.x - pt_existing.x) * 107500.0
            distance_meters = (d_lat**2 + d_lng**2)**0.5

            if distance_meters <= threshold_meters:
                # Corroborating report detected!
                incident["report_count"] = incident.get("report_count", 1) + 1
                incident["last_corroborated_at"] = now.isoformat()
                incident["confidence"] = min(0.98, incident["confidence"] + 0.25)
                
                if incident["report_count"] >= 2 and incident["status"] == "REPORTED":
                    incident["status"] = "VERIFIED"
                
                return {
                    "action": "CORROBORATED",
                    "incident_id": incident["id"],
                    "confidence": incident["confidence"],
                    "status": incident["status"]
                }

        # No nearby cluster found; create new candidate incident
        new_report["report_count"] = 1
        new_report["confidence"] = 0.35 if new_report.get("data_source") == "COMMUTER_REPORT" else 0.90
        new_report["status"] = "REPORTED" if new_report["confidence"] < 0.70 else "VERIFIED"
        return {"action": "CREATED", "incident": new_report}
```

---

## 3. Incident Lifecycle State Machine & Auto-Decay

```text
[REPORTED] ──(Multi-report Quorum)──> [VERIFIED] ──(Clearance Phase)──> [CLEARING] ──(Verified Clear)──> [RESOLVED]
     │                                     │                                 │
     └──(No Corroboration > 30m)──────────┴──(Half-life Decay Timeout)──────┴──> [EXPIRED]
```

### Auto-Decay Algorithm (Garbage Collection Worker)
Uncorroborated or stale reports must automatically decay so roads do not remain permanently blocked on the map.
- **Half-Life Decay Formula**:
  $$\text{Confidence}(t) = \text{Confidence}_0 \times e^{-\lambda (t - t_{\text{last\_corroborated}})}$$
  Where $\lambda = \frac{\ln(2)}{T_{\text{half}}}$ ($T_{\text{half}} = 20\text{ minutes}$ for unverified, $60\text{ minutes}$ for accidents).
- Once $\text{Confidence} < 0.15$, the background worker marks the incident as `EXPIRED` and drops it from the active routing graph.

---

## 4. Protected Incident Resolution (Anti-Griefing)

To prevent an attacker from clearing real active road hazards:
1. **Creation Token**: When a user submits an incident, the backend generates an ephemeral client session token (HMAC-SHA256 of `incident_id + client_salt`). Only a client presenting this token may unilaterally resolve the report within 15 minutes of submission.
2. **Community Verification Vote**: For all other anonymous users, resolving requires a confirmation vote ("Is this incident still there? [STILL THERE] / [ROAD CLEAR]"). When positive clearance votes exceed negative by $\ge 3$, status moves to `CLEARING` and then `RESOLVED`.

---

## 5. Viewport & Commuter Path Geofenced Streaming (SSE)

Instead of mobile clients polling `GET /api/v1/incidents` every 60 seconds, use **Server-Sent Events (SSE)** with viewport and route corridor geofencing:

```python
# Viewport and Route Buffer subscription pattern in FastAPI
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import asyncio

router = APIRouter()

@router.get("/api/v1/telemetry/stream")
async def stream_live_telemetry(
    request: Request,
    min_lng: float, min_lat: float, max_lng: float, max_lat: float,
    route_id: str | None = None
):
    """
    Streams live incident deltas and corridor speed shifts intersecting
    client viewport or the commuter's active route corridor buffer.
    """
    async def event_generator():
        client_bbox = (min_lng, min_lat, max_lng, max_lat)
        while True:
            if await request.is_disconnected():
                break
            
            # Fetch events intersecting bbox or commuter route buffer
            deltas = await get_spatial_deltas_for_bbox_or_route(client_bbox, route_id)
            if deltas:
                yield {
                    "event": "telemetry_delta",
                    "data": json.dumps(deltas)
                }
            
            # Send keep-alive comment every 15 seconds to prevent NAT gateway timeouts
            await asyncio.sleep(10)

    return EventSourceResponse(event_generator())
```

---

## 6. Verification & Quality Checklist

1. [ ] **Rate Limiting Active**: Verify IP rate limiter returns HTTP 429 when $> 5$ reports/min are sent from one IP.
2. [ ] **Input Bounds Check**: Verify coordinates outside `METRO_MANILA_STRICT_BBOX` return HTTP 422 with actionable error.
3. [ ] **Commuter Hazard Validation**: Verify incident endpoint accepts and validates pedestrian/commuter types (`PEDESTRIAN_OBSTRUCTION`, `FLOODED_SIDEWALK`, `TERMINAL_OVERCROWDING`).
4. [ ] **Anti-Griefing Resolution**: Verify anonymous users cannot unilaterally delete high-confidence verified incidents without a token or clearance quorum.
5. [ ] **Auto-Decay Active**: Verify stale uncorroborated incidents transition to `EXPIRED` within 30 minutes.
6. [ ] **Zero Emojis in Incident Feeds**: Verify severity tags use semantic text labels (`[SEVERE]`, `[MODERATE]`, `[CLEARING]`) and Google Material Symbols.

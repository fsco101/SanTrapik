---
name: traffic-geospatial-intelligence
description: Use when designing, querying, optimizing, or debugging geospatial telemetry, PostGIS spatial queries, OSRM/ORS multi-modal routing, corridor snapping, and bounding box validation
---

# Traffic Geospatial Intelligence

## Overview
SanTrapik is fundamentally a geospatial intelligence engine, not a simple map renderer. Road networks, traffic velocities, chokepoints, and road hazards are topological features anchored in coordinate space. This skill provides the spatial engineering standards, PostGIS query patterns, multi-modal Philippine routing profiles, and performance safeguards for urban traffic intelligence.

---

## 1. Coordinate Systems & Geodetic Precision

| Reference System | Identifier | Primary Usage in SanTrapik |
| :--- | :--- | :--- |
| **WGS 84** | `EPSG:4326` | Canonical database storage, GeoJSON interchange, GPS receiver coordinates (lon/lat degrees). |
| **Web Mercator** | `EPSG:3857` | Frontend MapLibre GL JS vector tile projection and raster basemaps. |
| **PRS92 / Philippines Zone 3** | `EPSG:3123` | Metric distance and buffer operations in Luzon / Metro Manila without latitude distortion. |

### Geodetic Rule: Avoid Degree-Based Distance Calculations
At Metro Manila's latitude ($\approx 14.5^\circ\text{N}$), $1^\circ$ of longitude is approximately $107.5\text{ km}$, while $1^\circ$ of latitude is approximately $110.6\text{ km}$. Never calculate metric distances using raw Pythagorean theorem on lon/lat degrees.
- Use `ST_DWithin(geom1::geography, geom2::geography, distance_in_meters)` for exact geodetic thresholding.
- Or use `ST_Transform(geom, 3123)` when performing complex metric buffer queries.

---

## 2. Bounding Box Guardrails & Geographic Defense

All coordinate inputs from client requests (origin, destination, viewport bounding boxes, report locations) MUST be strictly validated before invoking routing engines or PostGIS queries.

```python
# backend/app/core/spatial_guardrails.py
from typing import Tuple

# Bounding box encompassing Metro Manila and adjoining urban corridors (Bulacan/Rizal/Cavite fringes)
METRO_MANILA_STRICT_BBOX = (120.90, 14.35, 121.15, 14.80)  # min_lng, min_lat, max_lng, max_lat
GREATER_MANILA_OUTER_BBOX = (120.70, 14.15, 121.35, 15.00)

def validate_philippine_coordinate(lng: float, lat: float, strict: bool = True) -> bool:
    """Rejects out-of-bounds, NaN, or infinite coordinates to prevent PostGIS DoS."""
    if not (isinstance(lng, (int, float)) and isinstance(lat, (int, float))):
        return False
    min_lng, min_lat, max_lng, max_lat = METRO_MANILA_STRICT_BBOX if strict else GREATER_MANILA_OUTER_BBOX
    return (min_lng <= lng <= max_lng) and (min_lat <= lat <= max_lat)
```

---

## 3. High-Performance PostGIS Query Patterns

### Snapping Incidents & GPS Fixes to Road Centerlines
When an incident is reported or an OSRM route is evaluated, points must snap to the nearest road segment within a maximum tolerance (e.g. 50 meters).

```sql
-- Snap incident point to nearest arterial road segment within 50 meters
SELECT 
    rs.id AS segment_id,
    rs.road_name,
    rs.direction,
    ST_Distance(rs.geometry::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance_meters,
    ST_LineLocatePoint(rs.geometry, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) AS fraction_along_segment,
    ST_AsGeoJSON(ST_LineInterpolatePoint(rs.geometry, ST_LineLocatePoint(rs.geometry, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)))) AS snapped_geom
FROM road_segments rs
WHERE rs.geometry && ST_Expand(ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 0.001) -- GiST BBox filter
  AND ST_DWithin(rs.geometry::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 50.0)
ORDER BY distance_meters ASC
LIMIT 1;
```

### Spatial Indexing Rules (GiST)
Every table containing spatial geometry must declare a GiST index:
```sql
CREATE INDEX IF NOT EXISTS idx_road_segments_geom ON road_segments USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_incidents_geom ON incidents USING GIST(geometry);
```
**Rule:** Always include the bounding box operator (`&&`) or use indexed spatial predicates (`ST_DWithin`, `ST_Intersects`) so PostgreSQL performs an index scan instead of a catastrophic sequential table scan.

---

## 4. Multi-Modal Philippine Routing Profiles

Metro Manila's street dynamics require strict transport mode separation:

### 1. Private Automobile (`car`)
- Standard highway routing.
- May utilize expressways (Skyway Stages 1-3, SLEX, NLEX, NAIAX, CAVITEX, MCX) if `use_expressway=true`.
- Subject to MMDA Unified Vehicular Volume Reduction Program (UVVRP) number coding during peak hours (7:00-10:00 AM, 5:00-8:00 PM).

### 2. Motorcycles (`motorcycle`)
- **Tollway Restriction**: Barred by Toll Regulatory Board (TRB) / DOTr rules from elevated and at-grade expressways unless displacement is $\ge 400\text{cc}$.
- **Lane Filtering Velocity Differential**: In heavy arterial gridlock ($\le 15\text{ km/h}$ car speed), motorcycles maintain higher average velocities ($25\text{--}35\text{ km/h}$) due to lane splitting. Delay models must dampen congestion impact for motorcycle profiles.

### 3. Pedestrians (`walking`)
- Strictly excludes expressways, high-speed overpasses, and vehicular underpasses (e.g. EDSA-Shaw tunnel, EDSA-Ayala tunnel).
- Prefers routes with verified footbridges and sidewalks.

---

## 5. Corridor Speed & Harmonic Mean Aggregation

When aggregating speeds across multiple road segments along a route, **NEVER use the simple arithmetic mean**. Arithmetic averages significantly understate the time penalty of severe bottlenecks.

### The Correct Formula: Harmonic Distance-Weighted Velocity
Given $n$ segments with length $d_i$ and speed $v_i$:
$$v_{\text{route}} = \frac{\sum_{i=1}^n d_i}{\sum_{i=1}^n \frac{d_i}{v_i}}$$

```python
def calculate_harmonic_speed(segments: list[dict]) -> float:
    total_dist = sum(s["length_km"] for s in segments)
    total_time_hours = sum(s["length_km"] / max(s["speed_kmh"], 2.0) for s in segments)
    return round(total_dist / total_time_hours, 1) if total_time_hours > 0 else 0.0
```

---

## 6. Common Anti-Patterns to Avoid

| Anti-Pattern | Why It Breaks SanTrapik | Correct Approach |
| :--- | :--- | :--- |
| Calculating Euclidean distance on `(lng, lat)` | High latitude distortion; distances off by 30%+. | Use `ST_Distance(geom::geography)` or PRS92 `EPSG:3123`. |
| Unbounded spatial queries without GiST `&&` | Spikes PostgreSQL CPU to 100% under concurrent lookups. | Enforce bounding box index pruning (`ST_DWithin` / `&&`). |
| Allowing motorcycles on Skyway routes | Violates Philippine TRB law; gives illegal commute advice. | Force `use_expressway=False` unless motorcycle $\ge 400\text{cc}$. |
| Arithmetic mean for route average speed | Masks severe gridlock (1 km standstill + 9 km fast road = falsely high average). | Use distance-weighted Harmonic Mean speed. |
| Ingesting raw polylines without Ramer-Douglas-Peucker | Bloats GeoJSON responses to several megabytes on mobile networks. | Simplify polylines with `ST_SimplifyPreserveTopology(geom, 0.00005)`. |

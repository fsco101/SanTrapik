# SPEC.md — SanTrapik System Technical Specification

**System Name:** SanTrapik  
**Version:** 1.0.0-Draft  
**Status:** Approved for Implementation  
**Primary Focus:** Metro Manila, Philippines  
**Access Model:** Public, Anonymous Access (No Authentication Required)

---

## 1. Executive Summary & Problem Definition

### 1.1 The Context
Metro Manila experiences some of the densest traffic congestion in the world. Commuters and drivers routinely consult navigation apps, but existing solutions are designed primarily for **wayfinding** (how to get from Point A to Point B). When faced with red lines on a map, commuters are left with unanswered questions:
- *Why is this road red?* (Accident? Roadworks? Sudden flood? Normal rush hour surge?)
- *When did the incident start, and is it being cleared?*
- *How much delay will this actually add to my trip?*
- *When is this congestion expected to ease up?*

### 1.2 The SanTrapik Solution
SanTrapik is a **traffic intelligence and incident monitoring platform** that analyzes a commuter's selected route, decomposes it into constituent road segments, attaches verified real-time traffic and incident telemetry, and employs an AI/ML regression engine to forecast **congestion relief time**.

```text
[Start: Quezon City] ─── (Selected Route) ───> [Destination: Makati]
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Observed Conditions             Predicted Intelligence
   • Severity: Severe (EDSA)        • Delay: +32 minutes
   • Cause: Vehicular Accident       • Relief Window: 10:05 PM - 10:25 PM
   • Reported: 9:42 PM (MMDA)       • Confidence: 82%
   • Active Duration: 42 mins       • Alternative: C-5 (-16 min delay)
```

---

## 2. System Architecture

The SanTrapik architecture consists of four distinct decoupled tiers:

```text
+---------------------------------------------------------------------------------------+
|                                    CLIENT TIER                                        |
|  React 18 (Vite + TypeScript) + Tailwind CSS + MapLibre GL JS + Recharts              |
|  - Route Input & Selection              - Route Comparison & Segment Drilldown        |
|  - Real-time Metro Manila Heatmap       - Incident Timeline & Telemetry Badges        |
+-------------------------------------------+-------------------------------------------+
                                            │ HTTPS / JSON REST
                                            ▼
+---------------------------------------------------------------------------------------+
|                                  API GATEWAY TIER                                     |
|  FastAPI (Python 3.11+) + Pydantic v2 Schemas                                         |
|  - Rate Limiting & Input Validation      - Route Orchestrator                         |
|  - Incident Aggregator                   - ML Inference Bridge                        |
+---------------------+---------------------+---------------------+---------------------+
                      │                     │                     │
                      ▼                     ▼                     ▼
+---------------------+   +---------------------+   +---------------------+
|   ROUTING ENGINE    |   |  SPATIAL DATABASE   |   |   AI/ML INFERENCE   |
|  OSRM / ORS Engine  |   | PostgreSQL 15 +     |   | scikit-learn / ONNX |
|  - GeoJSON Polyline |   | PostGIS 3.3         |   | - Relief Predictor  |
|  - Maneuvers & Legs |   | - Spatial Indexing  |   | - Delay Estimator   |
+---------------------+   +---------------------+   +---------------------+
```

---

## 3. Database Schema (PostgreSQL + PostGIS)

All spatial tables use **EPSG:4326 (WGS 84)**.

### 3.1 `road_segments`
Stores physical road geometries partitioned into navigable segments.
```sql
CREATE TABLE road_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_name VARCHAR(128) NOT NULL,            -- e.g., "EDSA - Ortigas Segment"
    road_code VARCHAR(32),                      -- e.g., "AH26", "C-4"
    direction VARCHAR(32) NOT NULL,             -- "NB", "SB", "EB", "WB", "BOTH"
    city VARCHAR(64) NOT NULL,                  -- "Quezon City", "Mandaluyong", etc.
    baseline_speed_kmh NUMERIC(5, 2) NOT NULL,  -- Free-flow speed (e.g., 60.0 km/h)
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_road_segments_geom ON road_segments USING GIST(geometry);
CREATE INDEX idx_road_segments_road_name ON road_segments(road_name);
```

### 3.2 `traffic_records`
Time-series log of observed speeds and congestion metrics.
```sql
CREATE TABLE traffic_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_segment_id UUID NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    traffic_level VARCHAR(16) NOT NULL,         -- 'NORMAL', 'MODERATE', 'HEAVY', 'SEVERE'
    average_speed_kmh NUMERIC(5, 2) NOT NULL,
    congestion_percentage NUMERIC(5, 2),        -- 0.00 to 100.00%
    observed_at TIMESTAMPTZ NOT NULL,
    data_source VARCHAR(64) NOT NULL,           -- e.g., "MMDA_API", "CITY_TELEMETRY"
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_traffic_records_segment_time ON traffic_records(road_segment_id, observed_at DESC);
```

### 3.3 `incidents`
Verified active and historical road disruptions.
```sql
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_segment_id UUID REFERENCES road_segments(id) ON DELETE SET NULL,
    incident_type VARCHAR(64) NOT NULL,         -- 'ACCIDENT', 'ROADWORK', 'FLOOD', 'STALLED_VEHICLE'
    description TEXT,
    severity VARCHAR(16) NOT NULL,              -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- 'REPORTED', 'ACTIVE', 'CLEARING', 'RESOLVED'
    geometry GEOMETRY(Point, 4326) NOT NULL,
    reported_at TIMESTAMPTZ NOT NULL,
    cleared_at TIMESTAMPTZ,
    data_source VARCHAR(64) NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_incidents_geom ON incidents USING GIST(geometry);
CREATE INDEX idx_incidents_status ON incidents(status);
```

### 3.4 `predictions`
Historical and active outputs from the AI relief engine.
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_segment_id UUID NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    predicted_relief_time TIMESTAMPTZ NOT NULL,
    predicted_relief_minutes INTEGER NOT NULL,
    confidence_score NUMERIC(4, 3) NOT NULL,    -- 0.000 to 1.000
    model_version VARCHAR(32) NOT NULL,
    features_snapshot JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_segment ON predictions(road_segment_id, generated_at DESC);
```

### 3.5 `routes`
Caches calculated route polylines and segment associations.
```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_name VARCHAR(128) NOT NULL,
    destination_name VARCHAR(128) NOT NULL,
    origin_geom GEOMETRY(Point, 4326) NOT NULL,
    destination_geom GEOMETRY(Point, 4326) NOT NULL,
    route_geom GEOMETRY(LineString, 4326) NOT NULL,
    distance_meters NUMERIC(10, 2) NOT NULL,
    duration_seconds INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_routes_geom ON routes USING GIST(route_geom);
```

---

## 4. API Interface Specifications

Base URL: `/api/v1`

### 4.1 `POST /api/v1/route/analyze`
Generates route options, decomposes into road segments, and attaches traffic intelligence.

#### Request Body
```json
{
  "origin": {
    "name": "Quezon City Circle",
    "lat": 14.6515,
    "lng": 121.0494
  },
  "destination": {
    "name": "Ayala Triangle Gardens, Makati",
    "lat": 14.5573,
    "lng": 121.0234
  },
  "include_alternatives": true
}
```

#### Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "routes": [
      {
        "id": "rt_primary_edsa",
        "name": "via EDSA",
        "is_recommended": false,
        "summary": {
          "total_distance_km": 15.4,
          "estimated_travel_time_min": 84,
          "normal_travel_time_min": 52,
          "estimated_delay_min": 32,
          "overall_congestion": "SEVERE",
          "active_incidents_count": 2,
          "most_affected_segment": "EDSA - Ortigas Flyover"
        },
        "expected_relief": {
          "relief_time": "2026-09-09T22:20:00+08:00",
          "estimated_minutes_remaining": 38,
          "confidence": 0.82,
          "is_predicted": true
        },
        "geometry": {
          "type": "LineString",
          "coordinates": [[121.0494, 14.6515], [121.0491, 14.6508], "..."]
        },
        "segments": [
          {
            "segment_id": "seg_edsa_04",
            "name": "EDSA - Ortigas Flyover",
            "traffic_level": "SEVERE",
            "average_speed_kmh": 11.2,
            "congestion_percentage": 91.5,
            "incidents": [
              {
                "id": "inc_9821",
                "type": "ACCIDENT",
                "severity": "HIGH",
                "description": "2-vehicle collision occupying 2 middle lanes",
                "reported_at": "2026-09-09T21:42:00+08:00",
                "status": "ACTIVE"
              }
            ],
            "prediction": {
              "predicted_relief_time": "2026-09-09T22:20:00+08:00",
              "predicted_relief_minutes": 38,
              "confidence": 0.82
            },
            "last_updated": "2026-09-09T21:54:00+08:00"
          }
        ]
      },
      {
        "id": "rt_alt_c5",
        "name": "via C-5 Road",
        "is_recommended": true,
        "recommendation_reason": "Saves 16 minutes with fewer active incidents",
        "summary": {
          "total_distance_km": 17.1,
          "estimated_travel_time_min": 68,
          "normal_travel_time_min": 52,
          "estimated_delay_min": 16,
          "overall_congestion": "HEAVY",
          "active_incidents_count": 1,
          "most_affected_segment": "C-5 - Bagong Ilog"
        }
      }
    ]
  },
  "meta": {
    "server_time": "2026-09-09T21:55:00+08:00",
    "engine_version": "1.0.0"
  }
}
```

### 4.2 `GET /api/v1/traffic/heatmap`
Returns GeoJSON FeatureCollection of all monitored road segments in Metro Manila with active traffic states.

### 4.3 `GET /api/v1/incidents`
Returns filtered list of active incidents.
- Query Parameters: `city` (string), `type` (string), `severity` (string), `min_timestamp` (ISO8601).

### 4.4 `GET /api/v1/dashboard/stats`
Aggregated Metro Manila traffic metrics:
- `active_incidents`: integer
- `severe_roads_count`: integer
- `average_city_speed_kmh`: float
- `top_congested_arterials`: array of `{ road_name, congestion_percentage, expected_relief }`

---

## 5. Functional Requirements Traceability

| Req ID | Title | Description & Implementation Verification |
| :--- | :--- | :--- |
| **FR-01** | Route Input | Input starting point and destination via geocoding search or map pick. |
| **FR-02** | Route Generation | System invokes OSRM/ORS to generate valid, drivable GeoJSON routes. |
| **FR-03** | Segment Traffic Analysis | Segment route geometry and buffer with PostGIS to map traffic records. |
| **FR-04** | Congestion Classification | Classify speeds into `Normal`, `Moderate`, `Heavy`, `Severe` based on speed ratio: $Speed / Baseline$. |
| **FR-05** | Incident Display | Render verified road incidents within 50-meter buffer of route. |
| **FR-06** | Incident Timestamp | Display exact `reported_at` and `last_updated` times without fabrication. |
| **FR-07** | Travel Delay Estimation | Compute delay $= \text{Estimated Duration} - \text{Baseline Duration}$. |
| **FR-08** | Congestion Relief Prediction | Apply ML model to estimate `predicted_relief_minutes` and timestamp. |
| **FR-09** | Traffic Heatmap | Render interactive MapLibre vector heatmap of Metro Manila roads. |
| **FR-10** | Historical Analysis | Provide 7-day average congestion curves for selected segments via Recharts. |
| **FR-11** | Route Comparison | Present primary vs. alternative routes with delay and incident deltas. |
| **FR-12** | Traffic Dashboard | Provide macro-level Metro Manila traffic health indicators. |
| **FR-13** | Data Timestamping | Display visible telemetry freshness badges on all data cards. |
| **FR-14** | Public Anonymous Access | Guarantee zero auth gates for all public-facing endpoints. |

---

## 6. Machine Learning Model Specification

### 6.1 Objective Formulation
Predict the duration (in minutes) from current observation time $T_0$ until traffic speeds return to $\ge 70\%$ of the segment's baseline free-flow speed.
$$\hat{y} = f(X) \approx \Delta t_{\text{relief}} \quad (\text{minutes})$$

### 6.2 Feature Set ($X$)
1. **Segment Identifiers:** `segment_length`, `lanes_count`, `has_flyover`, `has_bus_lane`.
2. **Current Telemetry:** `current_speed_kmh`, `baseline_ratio` ($v_{curr} / v_{base}$), `congestion_level_encoded`.
3. **Temporal Features:** `hour_of_day` (sin/cos cyclic encoded), `day_of_week`, `is_weekend`, `is_payday_rush`.
4. **Incident Context:** `has_active_incident` (bool), `incident_type_encoded`, `incident_duration_minutes` ($T_0 - T_{\text{reported}}$), `incident_severity_weight`.
5. **Historical Dynamics:** `avg_historical_speed_at_hour`, `trend_delta_15m` ($v_{t} - v_{t-15m}$).

### 6.3 Algorithms & Evaluation
- **Candidate Models:** Random Forest Regressor, Gradient Boosting Regressor (LightGBM / XGBoost).
- **Evaluation Metrics:**
  - **MAE (Mean Absolute Error):** Primary metric. Target: MAE $\le 8.5$ minutes on test splits.
  - **RMSE (Root Mean Squared Error):** Penalizes extreme misforecasts.
  - **Relief Window Bounding:** System outputs a confidence window:
    $$[\hat{y} - 1.5 \cdot \text{MAE}, \hat{y} + 1.5 \cdot \text{MAE}]$$

---

## 7. Non-Functional Requirements

- **Performance:** Route analysis endpoint (`/route/analyze`) must return in $< 1200\text{ ms}$ under normal network load.
- **Data Integrity:** Strict enforcement of non-fabrication. When external sources lag, the UI displays `"Reported 45m ago"` rather than synthesizing modern fake events.
- **Geographic Bounding:** Restrict search queries to Metro Manila bounding box:
  `[120.90, 14.35, 121.15, 14.80]`.
- **Security:** Rate limiting per IP (e.g., 60 requests/minute) on public endpoints; CORS strictly configured for domain origins; SQL injection prevention via parameterized ORM queries.

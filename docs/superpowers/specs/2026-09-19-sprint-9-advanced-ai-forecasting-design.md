# Sprint 9: Advanced AI Congestion Relief & Spatiotemporal Forecasting Pipeline Design Specification

**Date**: 2026-09-19  
**Status**: Approved  
**Sprint**: Sprint 9 (SP9-001 to SP9-005)  
**Target Systems**: ML Pipeline, Backend FastAPI Services, MapLibre & React Frontend  

---

## 1. Executive Summary & Goals

SanTrapik's core differentiator is **predictive traffic intelligence**: forecasting **when** congestion will ease (`predicted_relief_minutes`) and diagnosing **what** is causing the bottleneck. 

Sprint 9 advances the ML engine from single-corridor regression to:
1. **Incident Clearance Duration Regression** (`SP9-001`): Specialized sub-model predicting physical clearance time ($T_{\text{clear}}$) based on blockage physics, tow dispatch, and geometry.
2. **Quantile Regression & Conformal Prediction Envelopes** (`SP9-002`): Replacing single-point estimates with $P_{10}, P_{50}, P_{90}$ bounded windows, dynamically scaling uncertainty during volatile conditions.
3. **Spatiotemporal Bottleneck Spillover Engine** (`SP9-003`): Topological road graph adjacency predicting upstream queue shockwaves (e.g. EDSA Shaw $\to$ Cubao in 15–20 mins) with cautionary amber map pulses.
4. **MLOps Drift Monitor & Fallback Circuit Breaker** (`SP9-004`): Tracking residuals, outlier rates, and tripling to deterministic empirical MMDA tables under severe drift or failure, exposed via `/api/v1/ml/status`.
5. **Frontend AI Prognosis Horizon Visualizer & Incident Drawer** (`SP9-005` & `SP9-001`): Slide-over `IncidentDrawer` with clearance confidence meter, and an interactive departure time scrubber (+0m, +15m, +30m, +45m, +60m) with electric indigo/cyan spectral branding.

---

## 2. Architecture & Subsystem Specifications

```
                           +-----------------------------------------------+
                           |          Raw Traffic & Incident Ingestion     |
                           +-----------------------+-----------------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           |      Feature Engineering & Graph Topology     |
                           |   - Cyclic Temporal & Diurnal Rush Features   |
                           |   - Blockage Ratio & Tow Dispatch Status      |
                           |   - Directional Road Adjacency Graph          |
                           +-------+-------------------------------+-------+
                                   |                               |
                   +---------------+                               +---------------+
                   v                                                               v
+------------------------------------+                           +------------------------------------+
|  SP9-001: Incident Clearance Model |                           |  SP9-003: Spatiotemporal Spillover |
|  - HistGradientBoostingRegressor   |                           |  - Directional Queue Shockwaves    |
|  - Target: MAE <= 7.0 mins         |                           |  - Upstream Segments Flagging      |
|  - Predicts physical clearance     |                           |  - Proactive Commuter Warnings     |
+------------------+-----------------+                           +-----------------+------------------+
                   |                                                               |
                   +-------------------------------+-------------------------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           |   SP9-002: Quantile Corridor Relief Engine    |
                           |   - P10 (Optimistic), P50 (Median), P90 (Max) |
                           |   - Dynamic Uncertainty (P90 - P10)           |
                           |   - Confidence Inversely Scaled               |
                           +-----------------------+-----------------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           |   SP9-004: MLOps Drift & Circuit Breaker      |
                           |   - Rolling Residual & Outlier Monitoring     |
                           |   - Circuit Breaker: OPERATIONAL / FALLBACK   |
                           |   - Deterministic MMDA Fallback Table         |
                           +-----------------------+-----------------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           |        FastAPI Route Analysis Endpoints       |
                           |        (/api/v1/route/analyze & /ml/status)   |
                           +-----------------------+-----------------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           |           Frontend Telemetry & UI             |
                           |   - Slide-over IncidentDrawer.tsx             |
                           |   - AI Prognosis Slider (+0m to +60m)         |
                           |   - MapLibre Pulsing Amber Spillover Layer    |
                           +-----------------------------------------------+
```

---

## 3. Detailed Component Design

### 3.1 SP9-001: Incident Clearance Duration Regression Sub-Model
* **Script**: `ml/pipelines/train_clearance_model.py`
* **Target Variable**: `incident_clearance_minutes` (elapsed time until all blocked lanes are reopened).
* **Input Features**:
  1. `incident_type_code`: Ordinal encoded (`STALLED_VEHICLE=1`, `COLLISION_MINOR=2`, `COLLISION_MULTI=3`, `ROADWORK=4`, `FLOOD=5`).
  2. `lanes_blocked`: Number of blocked lanes (1 to 4).
  3. `road_width_lanes`: Total corridor lane capacity (2 to 6).
  4. `blockage_ratio`: $\frac{\text{lanes\_blocked}}{\text{road\_width\_lanes}}$.
  5. `tow_truck_dispatched`: Binary (0 = pending/en route, 1 = on scene).
  6. `peak_hour`: Binary indicator (0 or 1).
  7. `heavy_vehicle_involved`: Binary indicator (e.g. public bus, container truck).
* **Algorithm**: `HistGradientBoostingRegressor(max_iter=150, learning_rate=0.08, min_samples_leaf=15, random_state=42)` targeting **MAE $\le 7.0$ minutes**.
* **Artifact Output**: `ml/models/incident_clearance_model.joblib` and mirrored to `backend/app/ml/artifacts/incident_clearance_model.joblib`.
* **Corridor Relief Integration**: `PredictionService` feeds $T_{\text{clear}}$ into segment friction recovery decay curves.

### 3.2 SP9-002: Quantile Regression & Conformal Envelopes
* **Quantile Training**:
  * Fit 3 regressors using pinball loss `loss='quantile'`:
    * $\alpha = 0.10 \implies P_{10}$ (optimistic rapid recovery).
    * $\alpha = 0.50 \implies P_{50}$ (median expectation).
    * $\alpha = 0.90 \implies P_{90}$ (pessimistic protracted delay).
* **Uncertainty & Confidence Scaling**:
  $$\text{Interval Width } \Delta = P_{90} - P_{10}$$
  $$\text{Confidence Score} = \max\left(0.50, \min\left(0.96, 1.0 - \frac{\Delta}{120.0}\right)\right)$$
* **Guardrails**:
  * $P_{10} \ge 5.0\text{ minutes}$.
  * $P_{50} = \max(P_{10}, P_{50})$.
  * $P_{90} = \max(P_{50}, P_{90})$.
  * Output schema fields: `p10_optimistic_mins`, `p50_median_mins`, `p90_pessimistic_mins`, `relief_window_display` (e.g. `"~25–40 mins"`).

### 3.3 SP9-003: Spatiotemporal Bottleneck Spillover Engine
* **File**: `backend/app/services/spillover.py`
* **Graph Structure**: Directional adjacency graph of Metro Manila corridors (EDSA NB/SB, C5 NB/SB, Commonwealth, Quezon Ave, Roxas Blvd).
* **Shockwave Physics**:
  * Shockwave propagation velocity $v_w \approx 12\text{--}18\text{ km/h}$ upstream against traffic flow.
  * Trigger: Segment congestion $\ge 60\%$ or speed ratio $< 0.35$ or active severe incident.
  * Shockwave propagates to immediate upstream contiguous segments within $15\text{--}45$ minutes.
* **Response Payload**:
  * `spillover_warnings`: Array of user-facing notices (e.g. `["Upstream slowdown expected at Cubao in ~15 mins due to EDSA Shaw bottleneck"]`).
  * `spillover_segments`: Array of segment IDs experiencing backpressure.

### 3.4 SP9-004: MLOps Drift Monitor & Circuit Breaker
* **File**: `backend/app/services/drift_monitor.py`
* **Continuous Evaluation**:
  * Asynchronous circular buffer tracking last 200 inference inputs and ground-truth comparisons.
  * Rolling 1-hour MAE and outlier input rates.
* **Circuit Breaker State Machine**:
  * `OPERATIONAL`: Rolling MAE $\le 15.0$ mins, outlier rate $\le 20\%$.
  * `DEGRADED`: Outlier rate $> 20\%$. Bounding intervals expanded, confidence discounted.
  * `FALLBACK`: Rolling MAE $> 15.0$ mins or ML pipeline exception. Trips immediately to deterministic MMDA empirical lookup table.
* **Endpoints**:
  * `GET /api/v1/ml/status` returning `{ status: "OPERATIONAL" | "DEGRADED" | "FALLBACK", rolling_mae_minutes: float, inferences_last_hour: int, active_model_version: str }`.
  * Integrated into `/api/v1/health`.

### 3.5 SP9-005 & SP9-001: Frontend AI Prognosis Horizon & Slide-Over Drawer
* **`IncidentDrawer.tsx`**:
  * Slide-over right drawer opening on incident click.
  * Shows incident type, clearance countdown, P10/P50/P90 interval window, lanes blocked, tow dispatch status, and electric indigo/cyan confidence meter.
* **`RouteIntelligenceCard.tsx`**:
  * Prognosis departure scrubber: `+0m (Now)`, `+15m`, `+30m`, `+45m`, `+60m`.
  * Header badge: `[AI FORECAST: DEPARTURE +30M]`.
  * Dynamically updates segment velocities and delay estimates across the forecast horizon.
* **`MapContainer.tsx`**:
  * Pulsing amber MapLibre GeoJSON layer for `spillover_segments`.

---

## 4. Verification Plan

### Automated Tests
1. **Clearance Model Unit Test**:
   * Run `ml/pipelines/train_clearance_model.py` and verify MAE $\le 7.0$ minutes and model artifact creation.
2. **Quantile Bounds & Guardrails Test**:
   * Test `backend/app/ml/inference.py` ensuring $P_{10} \le P_{50} \le P_{90}$, all non-negative, and confidence score inversely correlates with interval width.
3. **Spillover Graph Test**:
   * Unit test `backend/app/services/spillover.py` asserting upstream segments are correctly flagged when a downstream choke point is triggered.
4. **Circuit Breaker Test**:
   * Test `backend/app/services/drift_monitor.py` by simulating high-residual inputs and verifying automatic fallback to MMDA heuristic table.
5. **Frontend Build & Lint**:
   * Run `npm run build` in `frontend/` to ensure zero TypeScript or bundling errors.

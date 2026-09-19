# Sprint 9: Advanced AI Congestion Relief & Spatiotemporal Forecasting Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Advance SanTrapik's ML inference pipeline with an incident clearance sub-model, probabilistic quantile relief envelopes ($P_{10}/P_{50}/P_{90}$), directional graph bottleneck spillover shockwave modeling, continuous drift detection with empirical fallback circuit breaker, and an interactive frontend AI prognosis horizon visualizer with a slide-over incident drawer.

**Architecture:** 
1. `ml/pipelines/train_clearance_model.py` trains `HistGradientBoostingRegressor` predicting physical clearance duration (target: MAE $\le 7.0$ mins).
2. `backend/app/ml/inference.py` and `guardrails.py` implement multi-quantile pinball loss estimation ($P_{10}/P_{50}/P_{90}$) with dynamic uncertainty intervals.
3. `backend/app/services/spillover.py` evaluates directional graph adjacency along Metro Manila arterials to project upstream queuing shockwaves over 15–45 minutes.
4. `backend/app/services/drift_monitor.py` tracks inference residuals and outlier rates, automatically tripping to deterministic MMDA lookup tables under drift.
5. `frontend/src/components/incident/IncidentDrawer.tsx` and `RouteIntelligenceCard.tsx` provide interactive clearance telemetry, departure time scrubbing (+0m to +60m), and pulsing amber spillover map layers.

**Tech Stack:** Python 3.11+, Scikit-Learn, Joblib, FastAPI, Pydantic v2, Shapely, React 19, TypeScript, Tailwind CSS, MapLibre GL.

**Spec:** `docs/superpowers/specs/2026-09-19-sprint-9-advanced-ai-forecasting-design.md`

## Global Constraints
- Target clearance MAE $\le 7.0$ minutes on test set.
- Target corridor relief inference latency $\le 15.0$ ms.
- Guardrail: Non-negative lower bounds under all conditions ($P_{10} \ge 5.0$, $P_{50} \ge P_{10}$, $P_{90} \ge P_{50}$).
- Circuit breaker trips when rolling 1-hour MAE $> 15.0$ mins or outlier rate $> 20\%$.
- Frontend electric glow aesthetics: Cyan (`#06B6D4`) and Indigo (`#6366F1`) for AI forecasts; Amber (`#F59E0B`) for spillover shockwave warnings.

---

### Task 1: Incident Clearance Duration Regression Pipeline (SP9-001)

**Files:**
- Create: `ml/pipelines/train_clearance_model.py`
- Create: `backend/tests/test_clearance_model.py`
- Modify: `backend/app/ml/inference.py`
- Artifacts: `ml/models/incident_clearance_model.joblib`, `backend/app/ml/artifacts/incident_clearance_model.joblib`

**Interfaces:**
- Produces: `ml/models/incident_clearance_model.joblib` and `predict_incident_clearance(incident: dict) -> float`
- Consumes: Raw incident dictionaries (`incident_type`, `lanes_blocked`, `tow_truck_dispatched`, `road_width_lanes`).

- [ ] **Step 1: Write test for incident clearance training and prediction**
Create `backend/tests/test_clearance_model.py` verifying model fits with MAE $\le 7.0$ minutes and produces realistic clearance predictions.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_clearance_model.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement training pipeline in `ml/pipelines/train_clearance_model.py`**
Implement dataset generation reflecting Metro Manila incident clearance physics, train `HistGradientBoostingRegressor`, evaluate MAE, and serialize to `ml/models/` and `backend/app/ml/artifacts/`.

- [ ] **Step 4: Integrate clearance model into `backend/app/ml/inference.py`**
Load `incident_clearance_model.joblib` in `PredictionService` and incorporate clearance duration into segment relief calculations.

- [ ] **Step 5: Run tests to verify they pass**
Run: `pytest backend/tests/test_clearance_model.py -v`
Expected: PASS with MAE $\le 7.0$ mins.

- [ ] **Step 6: Commit**
```bash
git add ml/pipelines/train_clearance_model.py backend/tests/test_clearance_model.py backend/app/ml/inference.py
git commit -m "feat(ml): implement incident clearance duration regression pipeline (SP9-001)"
```

---

### Task 2: Quantile Regression & Conformal Prediction Envelopes (SP9-002)

**Files:**
- Modify: `backend/app/ml/train.py`
- Modify: `backend/app/ml/inference.py`
- Modify: `backend/app/ml/guardrails.py`
- Modify: `backend/app/schemas/route.py`
- Create: `backend/tests/test_quantile_relief.py`

**Interfaces:**
- Produces: `format_quantile_relief(p10: float, p50: float, p90: float, features: np.ndarray) -> dict` with `p10_optimistic_mins`, `p50_median_mins`, `p90_pessimistic_mins`, `relief_window_display`, and confidence score.
- Consumes: Multi-segment features array from `batch_extract_features`.

- [ ] **Step 1: Write unit tests for quantile inference and interval bounding**
Create `backend/tests/test_quantile_relief.py` asserting $P_{10} \le P_{50} \le P_{90}$, non-negative lower bounds, confidence inversely scaling with interval width, and format window display.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_quantile_relief.py -v`
Expected: FAIL (missing fields / assertion failures)

- [ ] **Step 3: Update `backend/app/ml/guardrails.py` and `backend/app/schemas/route.py`**
Add `p10_optimistic_mins`, `p50_median_mins`, `p90_pessimistic_mins`, and `relief_window_display` to `ExpectedRelief` schema and update guardrails.

- [ ] **Step 4: Update `backend/app/ml/inference.py` with multi-quantile estimators**
Support pinball loss quantile regression models for corridor relief forecasting.

- [ ] **Step 5: Run test to verify it passes**
Run: `pytest backend/tests/test_quantile_relief.py -v`
Expected: PASS

- [ ] **Step 6: Commit**
```bash
git add backend/app/ml/ backend/app/schemas/route.py backend/tests/test_quantile_relief.py
git commit -m "feat(ml): implement quantile regression envelopes P10/P50/P90 (SP9-002)"
```

---

### Task 3: Spatiotemporal Bottleneck Spillover Engine (SP9-003)

**Files:**
- Create: `backend/app/services/spillover.py`
- Modify: `backend/app/services/spatial.py`
- Modify: `backend/app/schemas/route.py`
- Modify: `backend/app/api/v1/endpoints/route.py`
- Create: `backend/tests/test_spillover.py`

**Interfaces:**
- Produces: `evaluate_corridor_spillover(segments: List[dict], active_incidents: List[dict]) -> Tuple[List[str], List[str]]`
- Consumes: Monitored segments and incident locations along the corridor.

- [ ] **Step 1: Write unit test for directional spillover propagation**
Create `backend/tests/test_spillover.py` testing upstream shockwave flagging when a severe downstream bottleneck exists (e.g. EDSA Shaw $\to$ Cubao).

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_spillover.py -v`
Expected: FAIL (spillover service not implemented)

- [ ] **Step 3: Implement `backend/app/services/spillover.py`**
Implement directional road adjacency graph and LWR backpressure shockwave calculation.

- [ ] **Step 4: Integrate spillover evaluation into `backend/app/services/spatial.py` and route schemas**
Add `spillover_warnings` and `spillover_segments` to `RouteItem` schema and include in route analysis response.

- [ ] **Step 5: Run test to verify it passes**
Run: `pytest backend/tests/test_spillover.py -v`
Expected: PASS

- [ ] **Step 6: Commit**
```bash
git add backend/app/services/spillover.py backend/app/services/spatial.py backend/app/schemas/route.py backend/app/api/v1/endpoints/route.py backend/tests/test_spillover.py
git commit -m "feat(spatial): implement spatiotemporal bottleneck spillover predictor (SP9-003)"
```

---

### Task 4: MLOps Drift Monitor & Circuit Breaker (SP9-004)

**Files:**
- Create: `backend/app/services/drift_monitor.py`
- Modify: `backend/app/ml/inference.py`
- Modify: `backend/app/api/v1/endpoints/health.py`
- Modify: `backend/app/api/v1/api.py`
- Create: `backend/tests/test_drift_monitor.py`

**Interfaces:**
- Produces: `drift_monitor.record_inference(...)`, `drift_monitor.get_status()`, endpoint `GET /api/v1/ml/status`.
- Consumes: Features, predictions, and ground-truth observations.

- [ ] **Step 1: Write unit test for drift monitor and circuit breaker**
Create `backend/tests/test_drift_monitor.py` testing residual tracking, outlier tracking, and state transitions (`OPERATIONAL` $\to$ `FALLBACK`).

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_drift_monitor.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `backend/app/services/drift_monitor.py`**
Build rolling evaluation window, threshold evaluation (MAE $> 15$ mins), and empirical MMDA fallback table trigger.

- [ ] **Step 4: Integrate with `backend/app/ml/inference.py` and expose `/api/v1/ml/status`**
Record inference calls asynchronously, enforce fallback when tripped, and expose status endpoint.

- [ ] **Step 5: Run test to verify it passes**
Run: `pytest backend/tests/test_drift_monitor.py -v`
Expected: PASS

- [ ] **Step 6: Commit**
```bash
git add backend/app/services/drift_monitor.py backend/app/ml/inference.py backend/app/api/v1/endpoints/health.py backend/app/api/v1/api.py backend/tests/test_drift_monitor.py
git commit -m "feat(mlops): implement model drift detection and fallback circuit breaker (SP9-004)"
```

---

### Task 5: Frontend AI Prognosis Visualizer, Spillover Map Pulse & Incident Drawer (SP9-005 & SP9-001)

**Files:**
- Create: `frontend/src/components/incident/IncidentDrawer.tsx`
- Modify: `frontend/src/components/telemetry/RouteIntelligenceCard.tsx`
- Modify: `frontend/src/components/map/MapContainer.tsx`
- Modify: `frontend/src/types/traffic.ts`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Produces:
  - `IncidentDrawer`: Slide-over drawer with clearance countdown, P10/P50/P90 interval, lanes blocked, and confidence meter.
  - Interactive departure scrubber (+0m, +15m, +30m, +45m, +60m) with `[AI FORECAST: DEPARTURE +X MIN]` badge.
  - Pulsing amber spillover layer on MapLibre.
- Consumes: `spillover_segments`, `spillover_warnings`, and quantile fields from `RouteItem`.

- [ ] **Step 1: Update TypeScript types in `frontend/src/types/traffic.ts`**
Add `p10_optimistic_mins`, `p50_median_mins`, `p90_pessimistic_mins`, `relief_window_display`, `spillover_warnings`, and `spillover_segments` to route and incident types.

- [ ] **Step 2: Build `frontend/src/components/incident/IncidentDrawer.tsx`**
Implement slide-over panel with physical clearance estimates, bounded windows, confidence meter, lanes blocked, and tow truck dispatch status.

- [ ] **Step 3: Update `frontend/src/components/telemetry/RouteIntelligenceCard.tsx`**
Add time slider (+0m, +15m, +30m, +45m, +60m), dynamic `[AI FORECAST: DEPARTURE +30M]` header badge, and wire up incident selection to trigger the drawer.

- [ ] **Step 4: Update `frontend/src/components/map/MapContainer.tsx`**
Add cautionary amber pulse styling for `spillover_segments`.

- [ ] **Step 5: Wire up state in `frontend/src/App.tsx` and verify build**
Run: `npm run build` in `frontend/`
Expected: Build passes with zero TypeScript or bundle errors.

- [ ] **Step 6: Commit**
```bash
git add frontend/src/
git commit -m "feat(frontend): implement incident drawer, prognosis horizon slider and map spillover pulse (SP9-001, SP9-003, SP9-005)"
```

---

### Task 6: End-to-End Verification & Documentation (Sprint 9 Acceptance)

**Files:**
- Modify: `sprints/sprint-9-advanced-ai-forecasting.json` (update status to completed)
- Create: `backend/tests/test_sprint9_e2e.py`

- [ ] **Step 1: Write and run end-to-end integration test**
Verify route analysis returns quantile relief, spillover warnings, incident clearance duration, and health check reports `OPERATIONAL`.

- [ ] **Step 2: Verify frontend builds cleanly**
Run: `npm run build` in `frontend/`

- [ ] **Step 3: Update `sprints/sprint-9-advanced-ai-forecasting.json`**
Mark issues SP9-001 through SP9-005 as completed.

- [ ] **Step 4: Commit**
```bash
git add sprints/sprint-9-advanced-ai-forecasting.json backend/tests/test_sprint9_e2e.py
git commit -m "chore(sprint-9): complete sprint 9 advanced AI forecasting pipeline"
```

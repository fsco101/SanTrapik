# SanTrapik Sprint Management

This directory contains the structured sprint specifications and issue tracking for the **SanTrapik** project. All sprints are defined in **JSON** format, aligned with [SPEC.md](../SPEC.md), [DESIGN/DESIGN.md](../DESIGN/DESIGN.md), [AGENT.md](../AGENT.md), and the specialized project skills in `.agents/skills/`.

All issues are tracked locally and synchronized with the GitHub repository: [fsco101/SanTrapik](https://github.com/fsco101/SanTrapik/issues).

---

## Sprint Roadmap & Issue Matrix

### [Sprint 1: Geospatial Database Architecture & Metro Manila Road Telemetry](./sprint-1-data-and-database.json)
* **Goal:** Set up PostgreSQL + PostGIS database, schema migrations, Metro Manila arterial road segments, real-time/historical traffic telemetry records, and incident tracking.
* **Status:** Completed
* **Issues:**
  - [#1: PostgreSQL + PostGIS Containerization & Core Schema Migrations](https://github.com/fsco101/SanTrapik/issues/1)
  - [#2: Metro Manila Major Arterials Road Network Ingestion](https://github.com/fsco101/SanTrapik/issues/2)
  - [#3: Traffic Records Telemetry Ingestion Pipeline & Seed Dataset](https://github.com/fsco101/SanTrapik/issues/3)
  - [#4: Road Incident Tracking Schema & Seed Data Ingestion](https://github.com/fsco101/SanTrapik/issues/4)

---

### [Sprint 2: FastAPI REST Services & Routing Engine Integration](./sprint-2-backend-services.json)
* **Goal:** Build the FastAPI backend, integrate OSRM/ORS for route generation, build PostGIS spatial snapping & incident intersection, and expose public REST APIs for route intelligence.
* **Status:** Completed
* **Issues:**
  - [#5: FastAPI Core Architecture, CORS, Health Checks & Pydantic v2 Schemas](https://github.com/fsco101/SanTrapik/issues/5)
  - [#6: Routing Engine Integration (OSRM / OpenRouteService)](https://github.com/fsco101/SanTrapik/issues/6)
  - [#7: Route Road-Segment Snapping & Spatial Intersect Service (PostGIS)](https://github.com/fsco101/SanTrapik/issues/7)
  - [#8: Route Intelligence Analysis Endpoint (`POST /api/v1/route/analyze`)](https://github.com/fsco101/SanTrapik/issues/8)
  - [#9: Traffic Heatmap, Incidents & City Dashboard REST Endpoints](https://github.com/fsco101/SanTrapik/issues/9)

---

### [Sprint 3: Frontend Implementation via Obsidian Telemetry Design](./sprint-3-frontend-ui.json)
* **Goal:** Build the React 18 + Vite + TypeScript web application strictly implementing the "Obsidian Telemetry" design system from the `DESIGN/` folder ([`DESIGN.md`](../DESIGN/DESIGN.md) and [`code.html`](../DESIGN/code.html)), MapLibre GL JS, Route Intelligence Card, and responsive layouts.
* **Status:** Completed
* **Issues:**
  - [#10: React + Vite + TypeScript Project Scaffolding with Obsidian Telemetry Tokens](https://github.com/fsco101/SanTrapik/issues/10)
  - [#11: MapLibre GL JS Interactive Map & Traffic Vector Layer Component](https://github.com/fsco101/SanTrapik/issues/11)
  - [#12: Route Search Bar, Waypoint Selector & Quick-Corridor Pills](https://github.com/fsco101/SanTrapik/issues/12)
  - [#13: Route Intelligence Card, Segment Velocity Bar & Incident Accordion](https://github.com/fsco101/SanTrapik/issues/13)
  - [#14: AI Relief Forecast Card, Confidence Meter & Telemetry Badges](https://github.com/fsco101/SanTrapik/issues/14)
  - [#15: Responsive Layout: Desktop Split Console & Mobile Bottom Telemetry Sheet](https://github.com/fsco101/SanTrapik/issues/15)

---

### [Sprint 4: AI/ML Congestion Relief Prediction Pipeline](./sprint-4-ai-ml-prediction.json)
* **Goal:** Develop, train, evaluate, and deploy the machine learning regression model to forecast congestion relief time (minutes to free-flow recovery) and integrate inference into the FastAPI backend.
* **Status:** Completed
* **Issues:**
  - [#16: Historical Traffic Feature Engineering & Dataset Preprocessing Pipeline](https://github.com/fsco101/SanTrapik/issues/16)
  - [#17: Relief Time Regression Model Training & Cross-Validation (MAE <= 8.5 min)](https://github.com/fsco101/SanTrapik/issues/17)
  - [#18: Model Serialization & FastAPI Inference Engine Integration](https://github.com/fsco101/SanTrapik/issues/18)
  - [#19: Prediction Confidence Interval Estimator & Guardrail Bounding](https://github.com/fsco101/SanTrapik/issues/19)

---

### [Sprint 5: System Integration, Route Comparison & Production Readiness](./sprint-5-integration-testing.json)
* **Goal:** Perform end-to-end integration between Frontend, Backend, Database, and ML model; implement alternative route comparison, real-time telemetry refreshing, Docker Compose multi-container setup, and production deployment readiness.
* **Status:** Completed
* **Issues:**
  - [#20: Alternative Route Comparison Logic & UI Recommendation Engine](https://github.com/fsco101/SanTrapik/issues/20)
  - [#21: Real-Time Telemetry Polling, Freshness Badges & Offline Handling](https://github.com/fsco101/SanTrapik/issues/21)
  - [#22: Docker Compose Full-Stack Environment & End-to-End Integration Verification](https://github.com/fsco101/SanTrapik/issues/22)
  - [#23: Performance Optimization (< 1200ms Latency), Security Audit & Production Build](https://github.com/fsco101/SanTrapik/issues/23)

---

### [Sprint 6: Security Hardening, Rate Limiting & Crowdsourced Incident Consensus Engine](./sprint-6-security-consensus.json)
* **Goal:** Eliminate critical vulnerabilities in the public anonymous model: sliding-window rate limiting, Pydantic v2 bounding box validation, spatiotemporal clustering (DBSCAN/quorum), anti-griefing resolution tokens, and half-life decay workers.
* **Status:** Completed
* **Issues:**
  - [#24: Strict Pydantic v2 Validation, Geographic Bounding Box Enforcement & Coordinate Sanitization](https://github.com/fsco101/SanTrapik/issues/24)
  - [#25: Sliding-Window IP & Fingerprint Rate Limiting for Spatial Endpoints](https://github.com/fsco101/SanTrapik/issues/25)
  - [#26: Spatiotemporal Incident Clustering & Corroboration Engine (150m / 15m Quorum)](https://github.com/fsco101/SanTrapik/issues/26)
  - [#27: Tamper-Resistant Incident Lifecycle & Protected Resolution (Reporter Token & Community Vote)](https://github.com/fsco101/SanTrapik/issues/27)
  - [#28: Automated Incident Aging, Half-Life Confidence Decay & Garbage Collection Worker](https://github.com/fsco101/SanTrapik/issues/28)

---

### [Sprint 7: Real-Time Geospatial Streaming & Viewport-Filtered Live Telemetry](./sprint-7-realtime-streaming.json)
* **Goal:** Upgrade from 60-second polling to persistent Server-Sent Events (SSE) and WebSockets, delivering low-latency geospatial event deltas filtered by client map viewport and active route buffer.
* **Status:** Planned
* **Issues:**
  - [#29: High-Throughput Server-Sent Events (SSE) Telemetry Stream Gateway](https://github.com/fsco101/SanTrapik/issues/29)
  - [#30: Viewport-Aware Geospatial Pub/Sub Channel Filtering (BBox Subscription)](https://github.com/fsco101/SanTrapik/issues/30)
  - [#31: Live Active Route Buffer Subscriptions & Real-Time Chokepoint Reroute Alerts](https://github.com/fsco101/SanTrapik/issues/31)
  - [#32: Frontend Streaming Hook (`useLiveTelemetryStream`) with Reconnect Backoff & Pulsar Telemetry](https://github.com/fsco101/SanTrapik/issues/32)
  - [#33: Dynamic Congestion Heatmap Vector Layer Streaming via GeoJSON Delta Updates](https://github.com/fsco101/SanTrapik/issues/33)

---

### [Sprint 8: Philippine Multi-Modal Commuter Intelligence & Corridor Economics](./sprint-8-multimodal-manila.json)
* **Goal:** Empower Metro Manila commuters with street-smart local intelligence: Expressway toll vs free surface cost-benefit analysis, motorcycle lane-filtering velocity adjustments, monsoon flood hazard warning integration, MMDA number coding advisories, and chokepoint cause diagnostics.
* **Status:** Planned
* **Issues:**
  - [#34: Skyway & Urban Expressway Toll Calculation Engine with Cost-Benefit Telemetry](https://github.com/fsco101/SanTrapik/issues/34)
  - [#35: Philippine Motorcycle Commute Telemetry (Arterial Lane Filtering & TRB 400cc Restrictions)](https://github.com/fsco101/SanTrapik/issues/35)
  - [#36: Metro Manila Monsoon & Flood Hazard Geo-Integration (PAGASA & Impassable Underpass Warnings)](https://github.com/fsco101/SanTrapik/issues/36)
  - [#37: MMDA Unified Vehicular Volume Reduction Program (UVVRP) Number Coding Checker & Route Advisory](https://github.com/fsco101/SanTrapik/issues/37)
  - [#38: Chokepoint Root Cause Diagnostics Decomposition](https://github.com/fsco101/SanTrapik/issues/38)

---

### [Sprint 9: Advanced AI Congestion Relief & Spatiotemporal Forecasting Pipeline](./sprint-9-advanced-ai-forecasting.json)
* **Goal:** Advance ML inference from simple corridor regression to incident clearance duration modeling, probabilistic quantile bounds (P10/P50/P90), upstream queue spillover prediction, and interactive time-horizon forecasting.
* **Status:** Planned
* **Issues:**
  - [#39: Incident Clearance Duration Regression Pipeline](https://github.com/fsco101/SanTrapik/issues/39)
  - [#40: Quantile Regression & Conformal Prediction Envelopes (P10, P50, P90 Relief Windows)](https://github.com/fsco101/SanTrapik/issues/40)
  - [#41: Spatiotemporal Bottleneck Spillover Predictor (Upstream Queue Propagation)](https://github.com/fsco101/SanTrapik/issues/41)
  - [#42: ML Model Drift Detection, Continuous Evaluation & Fallback Circuit Breaker](https://github.com/fsco101/SanTrapik/issues/42)
  - [#43: Frontend AI Prognosis Horizon Visualizer (Time Slider for +15m, +30m, +60m)](https://github.com/fsco101/SanTrapik/issues/43)

---

### [Sprint 10: High-Performance Vector Tile Caching, Spatial Redis Layers & Offline PWA Resilience](./sprint-10-performance-offline-pwa.json)
* **Goal:** Achieve sub-50ms hot corridor response times, implement PostGIS MVT dynamic vector tiles, add Redis spatial caching, and provide Progressive Web App (PWA) offline resilience for commuters facing spotty mobile connections.
* **Status:** Planned
* **Issues:**
  - [#44: Redis-Backed Ephemeral Spatial Caching for Hot Corridors & Route Analysis](https://github.com/fsco101/SanTrapik/issues/44)
  - [#45: PostGIS Mapbox Vector Tile (MVT) Dynamic Endpoint (`ST_AsMVT`)](https://github.com/fsco101/SanTrapik/issues/45)
  - [#46: Progressive Web App (PWA) Service Worker, Offline Asset Caching & Install Prompt](https://github.com/fsco101/SanTrapik/issues/46)
  - [#47: Saved Commute Corridors & Local Storage Telemetry Bookmarks](https://github.com/fsco101/SanTrapik/issues/47)
  - [#48: End-to-End Stress Testing, Sub-100ms Latency Verification & OWASP Security Audit](https://github.com/fsco101/SanTrapik/issues/48)

---

## Operating Protocol for AI Agents

1. **Active Sprint:** Always check `sprints/index.json` to identify the current active sprint.
2. **Dedicated Branching:** Follow the branch naming convention `sprint-<number>-<short-description>` branched from `main`.
3. **Specialized Skills:** When working on spatial, security, ML, or UI tasks, activate and adhere to the skills in `.agents/skills/`:
   - `traffic-geospatial-intelligence`
   - `incident-telemetry-resilience`
   - `traffic-prediction-mlops`
   - `obsidian-telemetry-ui`
4. **Verification Gate:** Run `py -m pytest backend/tests` and `npm run build` in `frontend/` before marking any issue as completed.

# SanTrapik Sprint Management

This directory contains the structured sprint specifications and issue tracking for the **SanTrapik** project. All sprints are defined in **JSON** format, aligned with [SPEC.md](../SPEC.md), [DESIGN/DESIGN.md](../DESIGN/DESIGN.md), and [AGENT.md](../AGENT.md).

All issues have been synchronized with the GitHub repository: [fsco101/SanTrapik](https://github.com/fsco101/SanTrapik/issues).

---

## Sprint Roadmap & Issue Matrix

### 🚀 [Sprint 1: Geospatial Database Architecture & Metro Manila Road Telemetry](./sprint-1-data-and-database.json)
* **Goal:** Set up PostgreSQL + PostGIS database, schema migrations, Metro Manila arterial road segments, real-time/historical traffic telemetry records, and incident tracking.
* **Status:** ✅ Completed
* **Issues:**
  - [#1: PostgreSQL + PostGIS Containerization & Core Schema Migrations](https://github.com/fsco101/SanTrapik/issues/1)
  - [#2: Metro Manila Major Arterials Road Network Ingestion](https://github.com/fsco101/SanTrapik/issues/2)
  - [#3: Traffic Records Telemetry Ingestion Pipeline & Seed Dataset](https://github.com/fsco101/SanTrapik/issues/3)
  - [#4: Road Incident Tracking Schema & Seed Data Ingestion](https://github.com/fsco101/SanTrapik/issues/4)

---

### ⚡ [Sprint 2: FastAPI REST Services & Routing Engine Integration](./sprint-2-backend-services.json)
* **Goal:** Build the FastAPI backend, integrate OSRM/ORS for route generation, build PostGIS spatial snapping & incident intersection, and expose public REST APIs for route intelligence.
* **Status:** ✅ Completed
* **Issues:**
  - [#5: FastAPI Core Architecture, CORS, Health Checks & Pydantic v2 Schemas](https://github.com/fsco101/SanTrapik/issues/5)
  - [#6: Routing Engine Integration (OSRM / OpenRouteService)](https://github.com/fsco101/SanTrapik/issues/6)
  - [#7: Route Road-Segment Snapping & Spatial Intersect Service (PostGIS)](https://github.com/fsco101/SanTrapik/issues/7)
  - [#8: Route Intelligence Analysis Endpoint (`POST /api/v1/route/analyze`)](https://github.com/fsco101/SanTrapik/issues/8)
  - [#9: Traffic Heatmap, Incidents & City Dashboard REST Endpoints](https://github.com/fsco101/SanTrapik/issues/9)

---

### 🎨 [Sprint 3: Frontend Implementation via Obsidian Telemetry Design](./sprint-3-frontend-ui.json)
* **Goal:** Build the React 18 + Vite + TypeScript web application strictly implementing the "Obsidian Telemetry" design system from the `DESIGN/` folder ([`DESIGN.md`](../DESIGN/DESIGN.md) and [`code.html`](../DESIGN/code.html)), MapLibre GL JS, Route Intelligence Card, and responsive layouts.
* **Status:** ✅ Completed
* **Issues:**
  - [#10: React + Vite + TypeScript Project Scaffolding with Obsidian Telemetry Tokens](https://github.com/fsco101/SanTrapik/issues/10)
  - [#11: MapLibre GL JS Interactive Map & Traffic Vector Layer Component](https://github.com/fsco101/SanTrapik/issues/11)
  - [#12: Route Search Bar, Waypoint Selector & Quick-Corridor Pills](https://github.com/fsco101/SanTrapik/issues/12)
  - [#13: Route Intelligence Card, Segment Velocity Bar & Incident Accordion](https://github.com/fsco101/SanTrapik/issues/13)
  - [#14: AI Relief Forecast Card, Confidence Meter & Telemetry Badges](https://github.com/fsco101/SanTrapik/issues/14)
  - [#15: Responsive Layout: Desktop Split Console & Mobile Bottom Telemetry Sheet](https://github.com/fsco101/SanTrapik/issues/15)

---

### 🧠 [Sprint 4: AI/ML Congestion Relief Prediction Pipeline](./sprint-4-ai-ml-prediction.json)
* **Goal:** Develop, train, evaluate, and deploy the machine learning regression model to forecast congestion relief time (minutes to free-flow recovery) and integrate inference into the FastAPI backend.
* **Status:** ✅ Completed
* **Issues:**
  - [#16: Historical Traffic Feature Engineering & Dataset Preprocessing Pipeline](https://github.com/fsco101/SanTrapik/issues/16)
  - [#17: Relief Time Regression Model Training & Cross-Validation (MAE <= 8.5 min)](https://github.com/fsco101/SanTrapik/issues/17)
  - [#18: Model Serialization & FastAPI Inference Engine Integration](https://github.com/fsco101/SanTrapik/issues/18)
  - [#19: Prediction Confidence Interval Estimator & Guardrail Bounding](https://github.com/fsco101/SanTrapik/issues/19)

---

### 🌐 [Sprint 5: System Integration, Route Comparison & Production Readiness](./sprint-5-integration-testing.json)
* **Goal:** Perform end-to-end integration between Frontend, Backend, Database, and ML model; implement alternative route comparison, real-time telemetry refreshing, Docker Compose multi-container setup, and production deployment readiness.
* **Status:** ⏳ Planned (Blocked by Sprint 3 & 4)
* **Issues:**
  - [#20: Alternative Route Comparison Logic & UI Recommendation Engine](https://github.com/fsco101/SanTrapik/issues/20)
  - [#21: Real-Time Telemetry Polling, Freshness Badges & Offline Handling](https://github.com/fsco101/SanTrapik/issues/21)
  - [#22: Docker Compose Full-Stack Environment & End-to-End Integration Verification](https://github.com/fsco101/SanTrapik/issues/22)
  - [#23: Performance Optimization (< 1200ms Latency), Security Audit & Production Build](https://github.com/fsco101/SanTrapik/issues/23)

---

## Operating Protocol for AI Agents

1. **Sprint Execution:** Follow the **Data-First Development Strategy** outlined in `AGENT.md`.
2. **Frontend Fidelity:** All frontend components must replicate the design system, colors, and layouts in [`DESIGN/`](../DESIGN/).
3. **Closing Issues:** When an issue is completed, mark its status as `"completed"` in the corresponding JSON file and close the issue on GitHub via `gh issue close <number>`.

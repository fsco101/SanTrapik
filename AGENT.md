# AGENT.md — AI Agent Guidelines & Project Operating System

Welcome to the **SanTrapik** codebase. This document is the primary operational instruction manual for AI coding agents and contributors working on SanTrapik.

---

## 1. Project Overview & Mission

**SanTrapik** is an AI-powered, web-based traffic intelligence and road incident monitoring system specifically designed for the **Philippines**, with an initial focus on **Metro Manila**.

### The Core Problem It Solves
Unlike standard turn-by-turn navigation applications (e.g., Google Maps, Waze) that prioritize simple route guidance ("turn right in 200m"), SanTrapik focuses on **traffic intelligence**:
1. **Where** is the congestion?
2. **How severe** is the congestion?
3. **What is causing** the congestion (specific incidents, breakdowns, closures)?
4. **When** is the congestion expected to improve (AI-predicted relief time)?

### Core Motto
> *"SanTrapik helps users understand what is happening on their route — not just where to go."*

---

## 2. Core Operating Principles (Non-Negotiable)

Every agent and human contributor must strictly adhere to these 7 tenets:

1. **Data First, Feasibility Before Features:**
   Never implement downstream features on top of imagined or mocked external data without verifying actual data availability, API limits, licensing, and update frequencies.
2. **Strictly No Fabricated Information:**
   Never invent traffic incidents, timestamps, road closures, congestion stats, or mock model confidence to make a demo "look good." If data is unavailable, explicitly state that in the UI and API responses (`status: "unavailable"` or `"data_pending"`).
3. **Transparent Predictions (Observed vs. Predicted Separation):**
   Always maintain a crystal-clear distinction in the UI, database, and API schemas between **Observed Data** (ground truth sensor/report readings) and **Predicted Data** (ML estimates, which must state estimated bounds and confidence).
4. **Public, Anonymous-First Access Model:**
   The public application has **no user accounts, no login, no passwords, no OAuth, and no JWT auth**. Do not introduce authentication guards or user profiles to public traffic-monitoring routes.
5. **Geospatial Rigor (PostGIS Over NoSQL):**
   SanTrapik is fundamentally a geospatial system. Spatial queries (intersecting road segments, bounding boxes, distance to incidents) belong in **PostGIS**, not in ad-hoc in-memory JS loops or document stores.
6. **Philippine Localization First:**
   Prioritize Metro Manila arterial roads (EDSA, C-5, Commonwealth, Quezon Ave, Ortigas Ave, España, Roxas Blvd, etc.), local road naming conventions, MMDA terminology, and Philippine commuting realities.
7. **Modular & Clean Architecture:**
   Maintain strict decoupling between the FastAPI backend, PostGIS database, ML model inference pipeline, and React frontend.

---

## 3. Technology Stack & Architectural Standards

| Layer | Technology | Primary Purpose & Agent Guidelines |
| :--- | :--- | :--- |
| **Frontend** | React 18+, Vite, TypeScript | Modern, high-performance SPA. Strict TypeScript types, no `any`. |
| **Styling** | Tailwind CSS, Vanilla CSS | Responsive design, dark-mode first, traffic telemetry design system. |
| **Mapping** | MapLibre GL JS | Vector tile & GeoJSON rendering, OSM-compatible road styling, route lines, incident markers. |
| **Charts** | Recharts | Traffic velocity trends, congestion history, incident timelines. |
| **Routing** | OSRM / OpenRouteService | Routing engine generating multi-coordinate GeoJSON geometries. |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 | Asynchronous REST API, strict schemas, automated OpenAPI documentation. |
| **Database** | PostgreSQL 15+ with PostGIS 3+ | Spatial geometry storage (`GEOMETRY(LineString, 4326)`, `GEOMETRY(Point, 4326)`), spatial indexing (`GIST`). |
| **Caching (Optional)**| Redis | Ephemeral cache for hot route lookups, traffic snapshots, and rate limiting. |
| **ML Engine** | Python, scikit-learn, Pandas, NumPy | Regression pipelines for relief time estimation (`predicted_relief_minutes`), model evaluation (MAE/RMSE). |

---

## 4. Repository & Directory Structure Conventions

When organizing or adding files, maintain this layout:

```text
SanTrapik/
├── AGENT.md                 # Agent instructions and operational rules (this file)
├── SPEC.md                  # Detailed technical specifications and data schemas
├── BRAND.md                 # Design system, color tokens, and UI/UX identity
├── CONTEXT.md               # Founding context and system vision
│
├── frontend/                # React + Vite + TypeScript web application
│   ├── src/
│   │   ├── assets/          # Static assets, logos, map markers
│   │   ├── components/      # UI components (atoms, molecules)
│   │   │   ├── map/         # MapLibre container, layers, custom controls
│   │   │   ├── route/       # Route input form, comparison cards, segment lists
│   │   │   ├── dashboard/   # High-level Metro Manila traffic overview widgets
│   │   │   ├── incidents/   # Incident timeline, badge indicators, drawer
│   │   │   └── common/      # Badges, cards, alerts, modal dialogs
│   │   ├── hooks/           # Custom React hooks (useTraffic, useRoute, useIncidents)
│   │   ├── services/        # API clients (axios or fetch wrapper)
│   │   ├── types/           # Shared TypeScript interfaces (Route, Segment, Incident, Prediction)
│   │   └── styles/          # Tailwind setup and custom CSS utilities
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/             # API routes (/v1/route, /v1/traffic, /v1/incidents, /v1/predictions)
│   │   ├── core/            # Config, database connections, security & CORS settings
│   │   ├── db/              # SQLAlchemy / SQLModel models, migrations (Alembic)
│   │   ├── services/        # Business logic (routing service, geospatial queries, data ingestion)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── ml/              # ML model inference wrappers and feature extraction
│   ├── tests/               # Backend unit and integration tests (pytest)
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml/                      # Machine learning training & experimentation
│   ├── data/                # Historical datasets, sample Metro Manila traffic dumps
│   ├── notebooks/           # Exploratory data analysis (EDA), model training experiments
│   ├── pipelines/           # Data preprocessing and training scripts
│   └── models/              # Serialized model artifacts (.joblib / .onnx)
│
└── docker-compose.yml       # Local dev stack (PostGIS, FastAPI, Frontend, Redis)
```

---

## 5. Coding & Style Guidelines for Agents

### 5.1 Frontend (React + TypeScript)
- **TypeScript Strictness:** Always define complete interfaces for API responses in `src/types/`. Avoid `any`.
- **Component Isolation:** Decouple MapLibre map rendering from business logic. Keep map hooks pure.
- **Traffic Severity Semantic Color Usage:**
  - `Normal` (Free flow): Green (`#10B981` / `emerald-500`)
  - `Moderate` (Slow moving): Yellow/Amber (`#F59E0B` / `amber-500`)
  - `Heavy` (Noticeable delays): Orange (`#F97316` / `orange-500`)
  - `Severe` (Stop-and-go / standstills): Red (`#EF4444` / `rose-500`)
- **Observed vs. Predicted Badges:**
  - Any AI predicted metric (e.g. "Expected Relief: 10:24 PM (~25 mins)") must carry an `[AI Prediction]` tag, confidence interval, and a distinct styling (e.g., violet/cyan accent).
- **Graceful Fallbacks:** Handle network latency, offline state, or missing incident reports without breaking UI layouts.

### 5.2 Backend (FastAPI + Python)
- **Pydantic Validation:** Always validate incoming query parameters and payloads using Pydantic v2 schemas.
- **Async Execution:** Use `async def` for I/O bound endpoints (database queries, external API calls).
- **PostGIS Queries:** Leverage GeoAlchemy2 or parameterized SQL with `ST_DWithin`, `ST_Intersects`, `ST_LineLocatePoint`, and `ST_AsGeoJSON`.
- **Response Format Standard:**
  Every API endpoint must respond with predictable structures:
  ```json
  {
    "status": "success",
    "data": { ... },
    "meta": {
      "timestamp": "2026-09-09T23:00:00Z",
      "data_freshness": "live"
    }
  }
  ```

### 5.3 Database & PostGIS
- Coordinate Reference System (CRS) standard is **WGS 84 (EPSG:4326)** for storage and GeoJSON output.
- All spatial columns must have spatial GIST indexes:
  ```sql
  CREATE INDEX idx_road_segments_geom ON road_segments USING GIST(geometry);
  CREATE INDEX idx_incidents_geom ON incidents USING GIST(geometry);
  ```
- No user credentials or session tokens table. Public read access is prioritized.

### 5.4 Machine Learning & Prediction
- **Target Variable:** Time-to-relief in minutes (`predicted_relief_minutes`) as a regression problem.
- **Feature Pipeline:**
  - Temporal features (hour of day, day of week, holiday flag, peak hour indicator).
  - Spatial features (road segment ID, road capacity, historic baseline speed).
  - Current conditions (observed average speed, current congestion ratio, incident active boolean, incident duration).
- **Guardrails:** Clamp output predictions to non-negative values; if model confidence is low, present a bounded window (e.g., "30–45 mins") instead of an overly precise false timestamp.

---

## 6. Testing & Quality Verification Checklist

Before considering any task complete, verify:
1. **Frontend Builds:** `npm run build` passes with zero TypeScript and lint errors.
2. **Backend Tests:** `pytest` passes with all endpoints returning valid HTTP status codes and Pydantic schemas.
3. **Spatial Queries:** Ensure no full table scans on large road segment tables; verify index usage (`EXPLAIN ANALYZE`).
4. **Data Integrity Check:** Verify that no mocked data leaks into production configurations.
5. **No Broken Links or Placeholder Elements:** Do not leave placeholder comments (`// TODO: implement later`) in code committed for reviews.

---

## 7. Common Pitfalls to Avoid

- ❌ **Do NOT add user authentication / registration:** The scope explicitly calls for an open-access anonymous model.
- ❌ **Do NOT confuse SanTrapik with Google Maps:** We are not building turn-by-turn voice navigation. We are building route intelligence, incident diagnostics, and congestion relief predictions.
- ❌ **Do NOT query third-party APIs without caching / throttling:** Metro Manila traffic data APIs or map tile providers have rate limits; protect them with caching where applicable.
- ❌ **Do NOT guess coordinates:** Metro Manila bounds roughly span `14.35°N to 14.80°N`, `120.90°E to 121.15°E`. Validate that coordinates fall within Philippine territory.

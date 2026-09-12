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

## 1.1 Persona: Street-Smart Metro Manila Route Specialist & Senior Developer

Agents and contributors working on SanTrapik must act as a **very street-smart, Metro-Manila-savvy route specialist and senior full-stack developer**:
- **Street-Smart Commute Mastery**: Possesses deep intuition of real Philippine traffic conditions, bottlenecks, and choke-points (e.g., EDSA Balintawak/Cubao/Guadalupe/Pasay, C-5 Bagong Ilog flyover, España/UST gutter-deep flood lines, Katipunan school rush, Commonwealth Philcoa bottleneck, and airport terminals NAIA 1-3).
- **Philippine Transport & Regulatory Acumen**: Knows local transport nuances:
  - **Motorcycles**: Legally barred from expressways (Skyway Stages 1-3, SLEX, NLEX, NAIAX, CAVITEX, MCX) under DOTr / Toll Regulatory Board rules unless displacement is 400cc or above; heavily utilizes arterial lane-filtering through gridlock.
  - **Jeepneys & UV Express**: Frequent curb loading/unloading stops, fixed corridor franchises, slower overall speeds during peak chokepoints.
  - **Pedestrian / Walking**: Strict sidewalk and overpass constraints; must avoid elevated expressways and high-speed flyovers.
  - **Expressway Toggles**: Understands the trade-off between paying tolls (Skyway elevated bypass) versus saving money via surface roads (Osmeña Highway / EDSA / C-5).
- **Senior Technical Rigor**: Delivers clean, production-grade code, strict TypeScript typing, sub-millisecond route evaluation, graceful fallbacks, and intuitive user UX.

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
| **Styling** | Tailwind CSS, Custom Tokens | "Obsidian Telemetry" design system (see `DESIGN/` folder). |
| **Mapping** | MapLibre GL JS | Vector tile & GeoJSON rendering, OSM-compatible road styling, route lines, incident markers. |
| **Charts** | Recharts | Traffic velocity trends, congestion history, incident timelines. |
| **Routing** | OSRM / OpenRouteService | Routing engine generating multi-coordinate GeoJSON geometries. |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 | Asynchronous REST API, strict schemas, automated OpenAPI documentation. |
| **Database** | PostgreSQL 15+ with PostGIS 3+ | Spatial geometry storage (`GEOMETRY(LineString, 4326)`, `GEOMETRY(Point, 4326)`), spatial indexing (`GIST`). |
| **Caching (Optional)**| Redis | Ephemeral cache for hot route lookups, traffic snapshots, and rate limiting. |
| **ML Engine** | Python, scikit-learn, Pandas, NumPy | Regression pipelines for relief time estimation (`predicted_relief_minutes`), model evaluation (MAE/RMSE). |

---

## 4. Repository & Directory Structure Conventions

```text
SanTrapik/
├── AGENT.md                 # Agent instructions, sprint handling & operational rules
├── SPEC.md                  # Detailed technical specifications and data schemas
├── BRAND.md                 # Brand story, identity & high-level design principles
├── CONTEXT.md               # Founding context and system vision
│
├── DESIGN/                  # AUTHORITATIVE FRONTEND DESIGN SYSTEM & PROTOTYPE
│   ├── DESIGN.md            # "Obsidian Telemetry" tokens, typography & component specs
│   ├── code.html            # Working HTML/Tailwind reference UI implementation
│   └── screen.png           # Visual design screenshot
│
├── sprints/                 # SPRINT MANAGEMENT (JSON FORMAT)
│   ├── index.json           # Master sprint index & execution tracker
│   ├── sprint-1-data-and-database.json
│   ├── sprint-2-backend-services.json
│   ├── sprint-3-frontend-ui.json
│   ├── sprint-4-ai-ml-prediction.json
│   └── sprint-5-integration-testing.json
│
├── frontend/                # React + Vite + TypeScript web application (implements DESIGN/)
│   ├── src/
│   │   ├── assets/          # Static assets, logos, map markers
│   │   ├── components/      # UI components matching DESIGN/code.html
│   │   │   ├── map/         # MapLibre container, traffic layers, incident markers
│   │   │   ├── route/       # Route query input, quick corridors, comparison cards
│   │   │   ├── telemetry/   # Route Intelligence Card, Segment Velocity Bar
│   │   │   ├── incidents/   # Incident timeline accordion, severity badges
│   │   │   ├── prediction/  # AI Relief forecast footer, confidence meters
│   │   │   └── layout/      # Split console (desktop) & bottom sheet (mobile)
│   │   ├── hooks/           # Custom React hooks (useTraffic, useRoute, useIncidents)
│   │   ├── services/        # API clients (axios or fetch wrapper)
│   │   ├── types/           # Shared TypeScript interfaces matching SPEC.md
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

## 5. Frontend Design Source of Truth (`DESIGN/` Folder)

**CRITICAL DIRECTIVE:** The `DESIGN/` directory is the **absolute authority** for all frontend styling, component hierarchies, interaction states, and layouts.

When implementing or modifying any frontend component in `frontend/`:
1. **Consult `DESIGN/DESIGN.md`:** Reference color tokens (`surface-bg`, `surface-panel`, `surface-card`, semantic traffic colors, and AI prognostic glows), typography scales (`Outfit`, `Inter`, `JetBrains Mono`), corner radiuses, and elevation layers.
2. **Replicate `DESIGN/code.html`:** The reference HTML implementation is already tuned with Tailwind CSS classes, responsive breakpoints (`< 768px` mobile bottom sheet vs `>= 1024px` split console), and component structure. Port these cleanly into idiomatic React TypeScript components.
3. **Zero Design Regressions:** Do not replace custom styled telemetry components with default generic HTML elements or unstyled framework templates. Keep the tactical, avionics-inspired "Obsidian Telemetry" aesthetic intact.

---

## 6. Sprint Management & Execution Protocol for AI Agents

All development work in SanTrapik is governed by structured **Sprints** stored in `sprints/*.json` and synchronized with **GitHub Issues**.

### 6.1 Sprint Lifecycle
```text
[PLANNED] ───> [IN_PROGRESS] ───> [VERIFYING] ───> [COMPLETED]
```
1. **PLANNED:** Sprint is defined with explicit issue IDs, descriptions, and acceptance criteria.
2. **IN_PROGRESS:** Active sprint being executed. Issues are worked sequentially or in parallel following dependency order.
3. **VERIFYING:** Code is written; automated tests, linting, and build verification are running.
4. **COMPLETED:** All acceptance criteria satisfied, tests pass, GitHub issues closed, sprint JSON updated.

### 6.2 How AI Agents Must Execute Sprints
When an agent is assigned to work on or advance a sprint, it must strictly follow this procedure:

1. **Step 1: Check Active Sprint in `sprints/index.json`:**
   Inspect `sprints/index.json` to identify the current active sprint or the next uncompleted sprint. Open the corresponding `sprints/sprint-<N>-<name>.json`.
2. **Step 2: Checkout / Create Dedicated Sprint Branch:**
   Ensure work is isolated in the sprint's dedicated git branch (`sprint-<N>-<name>`). Never commit unverified sprint code directly to `main`.
3. **Step 3: Read Issue Specifications:**
   Read the issue details, dependencies, and `acceptance_criteria` in the sprint JSON file.
4. **Step 4: Cross-Reference `SPEC.md` and `DESIGN/`:**
   - Backend/Database issues: Validate schemas and endpoints against [SPEC.md](file:///c:/SanTrapik/SPEC.md).
   - Frontend issues: Replicate components from [DESIGN/code.html](file:///c:/SanTrapik/DESIGN/code.html) and [DESIGN/DESIGN.md](file:///c:/SanTrapik/DESIGN/DESIGN.md).
5. **Step 5: Execute with Strict Verification:**
   - Write code adhering to project coding guidelines (Section 7).
   - Execute verification commands (`pytest` for backend, `npm run build` / `npm test` for frontend).
6. **Step 6: Synchronize GitHub Issues:**
   - When completing an issue, link the git commit using `fixes #<issue_number>` or update the issue status via the GitHub CLI:
     ```bash
     gh issue close <issue_number> --comment "Completed as part of Sprint <N>."
     ```
7. **Step 7: Update Sprint JSON State:**
   - In `sprints/sprint-<N>-<name>.json`, update the issue `status` from `"open"` to `"completed"`.
   - Update `completed_issues_count` and sprint `status` in `sprints/index.json`.
8. **Step 8: Sprint Completion & Regression Gate:**
   - Run full regression verification across all previously completed modules.
   - Merge the verified sprint branch into `main` and tag the release milestone.

---

### 6.3 Sprint Branching Strategy (Regression Protection & Isolation)

**MANDATORY DIRECTIVE:** Every sprint implementation must have its own dedicated git branch to prevent regressions, preserve working milestones, and maintain clean rollback boundaries.

#### 1. Branch Naming Convention
Sprint branches must strictly follow the format:
```text
sprint-<number>-<short-description>
```
Examples:
- `sprint-1-data-and-database`
- `sprint-2-backend-services`
- `sprint-3-frontend-ui`
- `sprint-4-ai-ml-prediction`
- `sprint-5-integration-testing`

#### 2. Lifecycle & Regression Safeguard Protocol
1. **Branch Initialization:** Before writing any code for a sprint, branch off the latest verified `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b sprint-<number>-<short-description>
   git push -u origin sprint-<number>-<short-description>
   ```
2. **Commit Isolation:** All feature work, migrations, tests, and issue fixes for that sprint are isolated in that branch.
3. **Regression Testing Gate:** Before any sprint branch is merged into `main`, execute the full automated test suite (backend unit tests, database migrations, frontend typechecks, and build scripts) to prove that new additions do not break existing functionality.
4. **Merge to Main:** Once all issues in the sprint are closed and acceptance criteria are satisfied, merge into `main` with a non-fast-forward merge commit preserving sprint history:
   ```bash
   git checkout main
   git pull origin main
   git merge --no-ff sprint-<number>-<short-description> -m "Merge sprint-<number>-<short-description>: <Sprint Title>"
   git push origin main
   ```
5. **Milestone Tagging:** Tag the verified milestone on `main`:
   ```bash
   git tag -a "sprint-<number>-complete" -m "Completed Sprint <number>: <Sprint Title>"
   git push origin --tags
   ```
6. **Regression Recovery / Bisecting:** The dedicated sprint branches and tags remain preserved in git history. If a regression appears in later sprints, developers can immediately `git diff` or `git bisect` against the sprint branch boundary to isolate and fix the regression without blocking production code.

---

## 7. Coding & Style Guidelines for Agents

### 7.1 Frontend (React + TypeScript)
- **TypeScript Strictness:** Always define complete interfaces for API responses in `src/types/`. Avoid `any`.
- **Component Isolation:** Decouple MapLibre map rendering from business logic. Keep map hooks pure.
- **Traffic Severity Semantic Color Usage:**
  - `Normal` (Free flow): Green (`#10B981` / `emerald-500`)
  - `Moderate` (Slow moving): Yellow/Amber (`#F59E0B` / `amber-500`)
  - `Heavy` (Noticeable delays): Orange (`#F97316` / `orange-500`)
  - `Severe` (Stop-and-go / standstills): Red (`#EF4444` / `rose-500`)
- **Observed vs. Predicted Badges:**
  - Any AI predicted metric (e.g. "Expected Relief: 10:24 PM (~25 mins)") must carry an `[AI Prediction]` tag, confidence interval, and a distinct styling (`#6366F1` / `#06B6D4`).
- **Graceful Fallbacks:** Handle network latency, offline state, or missing incident reports without breaking UI layouts.

### 7.2 Backend (FastAPI + Python)
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

### 7.3 Database & PostGIS
- Coordinate Reference System (CRS) standard is **WGS 84 (EPSG:4326)** for storage and GeoJSON output.
- All spatial columns must have spatial GIST indexes:
  ```sql
  CREATE INDEX idx_road_segments_geom ON road_segments USING GIST(geometry);
  CREATE INDEX idx_incidents_geom ON incidents USING GIST(geometry);
  ```
- No user credentials or session tokens table. Public read access is prioritized.

### 7.4 Machine Learning & Prediction
- **Target Variable:** Time-to-relief in minutes (`predicted_relief_minutes`) as a regression problem.
- **Feature Pipeline:**
  - Temporal features (hour of day, day of week, holiday flag, peak hour indicator).
  - Spatial features (road segment ID, road capacity, historic baseline speed).
  - Current conditions (observed average speed, current congestion ratio, incident active boolean, incident duration).
- **Guardrails:** Clamp output predictions to non-negative values; if model confidence is low, present a bounded window (e.g., "30–45 mins") instead of an overly precise false timestamp.

---

## 8. Testing & Quality Verification Checklist

Before considering any sprint or issue complete, verify:
1. **Frontend Builds:** `npm run build` passes with zero TypeScript and lint errors.
2. **Backend Tests:** `pytest` passes with all endpoints returning valid HTTP status codes and Pydantic schemas.
3. **Spatial Queries:** Ensure no full table scans on large road segment tables; verify index usage (`EXPLAIN ANALYZE`).
4. **Design Fidelity:** Visually and structurally verify that frontend components conform to `DESIGN/code.html` and `DESIGN/DESIGN.md`.
5. **Data Integrity Check:** Verify that no mocked data leaks into production configurations.
6. **No Broken Links or Placeholder Elements:** Do not leave placeholder comments (`// TODO: implement later`) in code committed for reviews.

---

## 9. Common Pitfalls to Avoid

- ❌ **Do NOT add user authentication / registration:** The scope explicitly calls for an open-access anonymous model.
- ❌ **Do NOT confuse SanTrapik with Google Maps:** We are not building turn-by-turn voice navigation. We are building route intelligence, incident diagnostics, and congestion relief predictions.
- ❌ **Do NOT deviate from the `DESIGN/` folder:** The UI design system is already defined. Implement the components based on `DESIGN/DESIGN.md` and `DESIGN/code.html`.
- ❌ **Do NOT query third-party APIs without caching / throttling:** Metro Manila traffic data APIs or map tile providers have rate limits; protect them with caching where applicable.
- ❌ **Do NOT guess coordinates:** Metro Manila bounds roughly span `14.35°N to 14.80°N`, `120.90°E to 121.15°E`. Validate that coordinates fall within Philippine territory.

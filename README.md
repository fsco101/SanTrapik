# SanTrapik
> **AI-Powered Metro Manila Traffic Intelligence & Road Incident Monitoring System**

SanTrapik is an intelligent traffic monitoring and congestion relief forecasting platform tailored specifically for the arterial corridors and bottleneck choke-points of Metro Manila (EDSA, C-5, Commonwealth, Quezon Ave, España, Roxas Blvd, and SLEX).

---

## System Architecture

- **Frontend**: React 19 + TypeScript + Vite + MapLibre GL + TailwindCSS (Obsidian Telemetry theme `#080C14`, `#0F172A`, `#1E293B`, `#6366F1`)
- **Backend API**: FastAPI + Uvicorn + Pydantic v2 + SQLAlchemy 2.0 (Psycopg 3)
- **Database & Spatial**: PostgreSQL 15 + PostGIS (WGS 84 EPSG:4326, Spatial GIST indexing)
- **AI/ML Engine**: Scikit-Learn `HistGradientBoostingRegressor` (Corridor Congestion Relief Time Predictor, MAE ~2.18 mins, inference latency < 15ms)
- **Routing**: Deterministic Metro Manila corridor graph with automatic public OSRM integration and route caching

---

## Quick Start with Docker Compose

To spin up the entire multi-container stack (Database, FastAPI Gateway, and Nginx Frontend):

```bash
docker-compose up --build
```

Services will be accessible at:
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173) or [http://localhost](http://localhost)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **PostGIS Database**: `localhost:5432` (`santrapik` / `postgres`)

---

## Local Development Setup

### 1. Backend

```bash
cd backend
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations & ingest road network geometry
alembic upgrade head
python scripts/ingest_roads.py
# Or optionally ingest live from OpenStreetMap Overpass:
# python scripts/ingest_osm_roads.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

---

## Automated Testing

### Backend & ML Tests
```bash
python -m pytest backend/tests/ -v
```
Includes:
- API endpoint integration tests (`test_api.py`)
- PostGIS schema & spatial distance tests (`test_database.py`)
- ML model training, cyclic features, and latency tests (`test_ml.py`)
- Full end-to-end pipeline, SLA latency (< 1200ms), and rate limiting verification (`test_e2e.py`)

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```
Builds an optimized production bundle with manual code-splitting (entry chunk gzip < 10 kB).

---

## Production Deployment Guide

### A. Frontend Deployment on Vercel

1. **Import Project**: Link your GitHub repository (`fsco101/SanTrapik`) on Vercel.
2. **Root Directory**: Set Root Directory to `frontend`.
3. **Framework Preset**: Select `Vite`.
4. **Environment Variables**:
   - `VITE_API_BASE_URL`: Set to your deployed backend URL (e.g., `https://santrapik-api.onrender.com`).
5. **Deploy**: Vercel will run `npm run build` and output to `dist/`.

### B. Backend Deployment on Render / Railway

#### Option 1: Render
1. **Managed PostgreSQL**:
   - Create a PostgreSQL database instance on Render.
   - Enable PostGIS: In PostgreSQL Shell, run `CREATE EXTENSION postgis; CREATE EXTENSION "uuid-ossp";`.
2. **Web Service**:
   - Connect repository and set root directory to `backend` or use Dockerfile.
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     - `DATABASE_URL`: `postgresql+psycopg://user:password@host:port/dbname`
     - `CORS_ORIGINS`: `["https://santrapik.vercel.app"]`
     - `RATE_LIMIT_PER_MINUTE`: `60`

#### Option 2: Railway
1. **Provision PostGIS**: Add PostgreSQL plugin and run `CREATE EXTENSION postgis;`.
2. **Deploy Backend**:
   - Deploy using the root `backend/Dockerfile`.
   - Connect `DATABASE_URL` reference variable.
   - Railway will auto-route incoming traffic to port 8000 with TLS.

---

## Security & Performance Features

- **Rate Limiting**: Custom sliding-window middleware enforcing a strict 60 requests/minute limit per client IP with `X-RateLimit-*` and `Retry-After` headers.
- **Route Caching**: In-memory deterministic corridor cache achieving p95 latency under 25ms.
- **Database Circuit-Breaker**: Graceful fallback to local GeoJSON dataset when database connectivity is degraded or offline.
- **Public Anonymous Access**: Zero login gates or authentication hurdles for public commuter visibility.

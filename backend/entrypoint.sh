#!/usr/bin/env sh
set -e

echo "=== SanTrapik Backend Container Initializing ==="

# Wait briefly for database to accept connections and apply Alembic migrations
if [ -n "$DATABASE_URL" ]; then
    echo "Applying database migrations with Alembic..."
    python -m alembic upgrade head || echo "Alembic upgrade warning: Continuing startup..."

    # Ingest baseline Metro Manila road segments if table is empty
    echo "Verifying baseline road network dataset..."
    python backend/scripts/ingest_roads.py || echo "Road network check complete."
fi

echo "=== Starting SanTrapik API Gateway on port ${PORT:-8000} ==="
exec uvicorn backend.app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"

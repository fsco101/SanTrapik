-- SanTrapik Core PostGIS Initialization Script
-- Coordinate Reference System: WGS 84 (EPSG:4326)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- 1. road_segments
CREATE TABLE IF NOT EXISTS road_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    road_name VARCHAR(128) NOT NULL,
    road_code VARCHAR(32),
    direction VARCHAR(32) NOT NULL,
    city VARCHAR(64) NOT NULL,
    baseline_speed_kmh NUMERIC(5, 2) NOT NULL,
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_road_segments_geom ON road_segments USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_road_segments_road_name ON road_segments(road_name);
CREATE INDEX IF NOT EXISTS idx_road_segments_city ON road_segments(city);

-- 2. traffic_records
CREATE TABLE IF NOT EXISTS traffic_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    road_segment_id UUID NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    traffic_level VARCHAR(16) NOT NULL, -- 'NORMAL', 'MODERATE', 'HEAVY', 'SEVERE'
    average_speed_kmh NUMERIC(5, 2) NOT NULL,
    congestion_percentage NUMERIC(5, 2),
    observed_at TIMESTAMPTZ NOT NULL,
    data_source VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traffic_records_segment_time ON traffic_records(road_segment_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_records_level ON traffic_records(traffic_level);

-- 3. incidents
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    road_segment_id UUID REFERENCES road_segments(id) ON DELETE SET NULL,
    incident_type VARCHAR(64) NOT NULL, -- 'ACCIDENT', 'ROADWORK', 'FLOOD', 'STALLED_VEHICLE'
    description TEXT,
    severity VARCHAR(16) NOT NULL,      -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- 'REPORTED', 'ACTIVE', 'CLEARING', 'RESOLVED'
    geometry GEOMETRY(Point, 4326) NOT NULL,
    reported_at TIMESTAMPTZ NOT NULL,
    cleared_at TIMESTAMPTZ,
    data_source VARCHAR(64) NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_geom ON incidents USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);

-- 4. predictions
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    road_segment_id UUID NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
    predicted_relief_time TIMESTAMPTZ NOT NULL,
    predicted_relief_minutes INTEGER NOT NULL,
    confidence_score NUMERIC(4, 3) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    features_snapshot JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_segment ON predictions(road_segment_id, generated_at DESC);

-- 5. routes
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_name VARCHAR(128) NOT NULL,
    destination_name VARCHAR(128) NOT NULL,
    origin_geom GEOMETRY(Point, 4326) NOT NULL,
    destination_geom GEOMETRY(Point, 4326) NOT NULL,
    route_geom GEOMETRY(LineString, 4326) NOT NULL,
    distance_meters NUMERIC(10, 2) NOT NULL,
    duration_seconds INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routes_geom ON routes USING GIST(route_geom);

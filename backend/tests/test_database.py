import os
import json
import pytest
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

from backend.app.core.config import settings
from backend.app.db.models import RoadSegment, TrafficRecord, Incident, Prediction, Route
from backend.scripts.seed_traffic import classify_traffic
from backend.scripts.seed_incidents import SAMPLE_INCIDENTS

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
GEOJSON_FILE = os.path.join(DATA_DIR, "metro_manila_roads.geojson")
SQL_INIT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts/init_db.sql"))

def test_geojson_validity_and_counts():
    """Verify GeoJSON dataset contains >= 50 arterial segments and valid coordinates."""
    assert os.path.exists(GEOJSON_FILE), f"GeoJSON file does not exist: {GEOJSON_FILE}"
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    assert len(features) >= 50, f"Expected at least 50 road segments, found {len(features)}"

    min_lng, min_lat, max_lng, max_lat = settings.METRO_MANILA_BBOX

    for feat in features:
        props = feat["properties"]
        geom = feat["geometry"]
        assert geom["type"] == "LineString"
        assert len(geom["coordinates"]) >= 2
        
        # Verify required fields
        assert "road_name" in props
        assert "direction" in props
        assert props["direction"] in ["NB", "SB", "EB", "WB", "BOTH"]
        assert "city" in props
        assert "baseline_speed_kmh" in props
        assert props["baseline_speed_kmh"] > 0

        # Validate bounding box
        for lng, lat in geom["coordinates"]:
            assert min_lng <= lng <= max_lng, f"Longitude {lng} out of Metro Manila bounds"
            assert min_lat <= lat <= max_lat, f"Latitude {lat} out of Metro Manila bounds"

def test_traffic_classification_thresholds():
    """Verify traffic classification speed-to-baseline ratios."""
    baseline = 60.0
    
    # >= 80% baseline -> NORMAL
    level, cong = classify_traffic(55.0, baseline)
    assert level == "NORMAL"
    assert cong <= 20.0
    
    # 50% - 79% baseline -> MODERATE
    level, cong = classify_traffic(36.0, baseline)
    assert level == "MODERATE"
    
    # 25% - 49% baseline -> HEAVY
    level, cong = classify_traffic(20.0, baseline)
    assert level == "HEAVY"
    
    # < 25% baseline -> SEVERE
    level, cong = classify_traffic(10.0, baseline)
    assert level == "SEVERE"
    assert cong >= 75.0

def test_incident_sample_definitions():
    """Verify incidents schema definitions, types, severities, and locations."""
    assert len(SAMPLE_INCIDENTS) >= 6
    min_lng, min_lat, max_lng, max_lat = settings.METRO_MANILA_BBOX

    valid_types = {"ACCIDENT", "ROADWORK", "FLOOD", "STALLED_VEHICLE"}
    valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    valid_statuses = {"REPORTED", "ACTIVE", "CLEARING", "RESOLVED"}

    for inc in SAMPLE_INCIDENTS:
        assert inc["incident_type"] in valid_types
        assert inc["severity"] in valid_severities
        assert inc["status"] in valid_statuses
        
        lng, lat = inc["point_lng_lat"]
        assert min_lng <= lng <= max_lng
        assert min_lat <= lat <= max_lat
        assert inc["data_source"]

def test_spatial_distance_and_proximity():
    """Verify spatial geometry calculations (Point to LineString proximity within buffer)."""
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Find EDSA Ortigas Flyover segment
    edsa_segment = None
    for feat in data["features"]:
        if "Ortigas Flyover" in feat["properties"]["road_name"]:
            edsa_segment = feat
            break

    assert edsa_segment is not None, "EDSA Ortigas segment not found in GeoJSON"
    
    line = LineString(edsa_segment["geometry"]["coordinates"])
    
    # Incident at EDSA Ortigas Flyover [121.0575, 14.5855]
    incident_point = Point(121.0575, 14.5855)
    
    # Geographic distance in degrees (~0.001 deg is approx 110 meters)
    deg_distance = line.distance(incident_point)
    # Proximity check: incident should be within ~0.005 degrees (~500m) of the segment line
    assert deg_distance < 0.005, f"Incident point too far from road segment: {deg_distance} deg"

def test_sql_ddl_and_indexes():
    """Verify init_db.sql contains all tables and required GIST spatial indexes."""
    assert os.path.exists(SQL_INIT_FILE)
    with open(SQL_INIT_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    expected_tables = ["road_segments", "traffic_records", "incidents", "predictions", "routes"]
    for tbl in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {tbl}" in sql_content, f"Missing table {tbl} in DDL"

    expected_indexes = [
        "idx_road_segments_geom",
        "idx_traffic_records_segment_time",
        "idx_incidents_geom",
        "idx_predictions_segment",
        "idx_routes_geom"
    ]
    for idx in expected_indexes:
        assert idx in sql_content, f"Missing index {idx} in DDL"

def test_orm_models_metadata():
    """Verify SQLAlchemy ORM class definitions and relationships."""
    assert RoadSegment.__tablename__ == "road_segments"
    assert TrafficRecord.__tablename__ == "traffic_records"
    assert Incident.__tablename__ == "incidents"
    assert Prediction.__tablename__ == "predictions"
    assert Route.__tablename__ == "routes"

    # Check relationships
    assert hasattr(RoadSegment, "traffic_records")
    assert hasattr(RoadSegment, "incidents")
    assert hasattr(RoadSegment, "predictions")
    assert hasattr(TrafficRecord, "road_segment")
    assert hasattr(Incident, "road_segment")

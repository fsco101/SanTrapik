import json
import os
import sys
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.config import settings
from backend.app.db.session import get_session_local, get_engine
from backend.app.db.models import RoadSegment

DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/metro_manila_roads.geojson"))

def validate_coordinates(coords, bbox):
    min_lng, min_lat, max_lng, max_lat = bbox
    for lng, lat in coords:
        if not (min_lng <= lng <= max_lng and min_lat <= lat <= max_lat):
            raise ValueError(f"Coordinate [{lng}, {lat}] is outside Metro Manila bounding box: {bbox}")

def ingest_roads(db: Session, geojson_path: str = DATA_FILE):
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"GeoJSON file not found at: {geojson_path}")
        
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    print(f"Loaded {len(features)} road segment features from GeoJSON.")
    
    inserted_count = 0
    updated_count = 0
    
    for feat in features:
        props = feat["properties"]
        geom = feat["geometry"]
        coords = geom["coordinates"]
        
        # 1. Validate bounding box
        validate_coordinates(coords, settings.METRO_MANILA_BBOX)
        
        # 2. Construct WKT LineString: "LINESTRING(lng lat, lng lat, ...)"
        wkt_coords = ", ".join([f"{lng} {lat}" for lng, lat in coords])
        wkt = f"LINESTRING({wkt_coords})"
        
        road_name = props["road_name"]
        road_code = props.get("road_code")
        direction = props["direction"]
        city = props["city"]
        baseline_speed = props["baseline_speed_kmh"]
        
        # 3. Check existing segment by road_name & direction
        existing = db.query(RoadSegment).filter(
            RoadSegment.road_name == road_name,
            RoadSegment.direction == direction
        ).first()
        
        if existing:
            existing.road_code = road_code
            existing.city = city
            existing.baseline_speed_kmh = baseline_speed
            existing.geometry = WKTElement(wkt, srid=4326)
            updated_count += 1
        else:
            segment = RoadSegment(
                road_name=road_name,
                road_code=road_code,
                direction=direction,
                city=city,
                baseline_speed_kmh=baseline_speed,
                geometry=WKTElement(wkt, srid=4326)
            )
            db.add(segment)
            inserted_count += 1
            
    db.commit()
    print(f"Road ingestion complete: {inserted_count} inserted, {updated_count} updated.")
    return inserted_count + updated_count

if __name__ == "__main__":
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    db = SessionLocal()
    try:
        count = ingest_roads(db)
        print(f"Total processed road segments: {count}")
    finally:
        db.close()

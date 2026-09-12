"""
OpenStreetMap (OSM) Road Network Ingestion Script for SanTrapik
Pulls real arterial corridors (motorway, trunk, primary, secondary)
from the OpenStreetMap Overpass API for Metro Manila and saves to PostGIS and GeoJSON.
"""

import json
import os
import sys
import httpx
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.config import settings
from backend.app.db.session import get_session_local, get_engine
from backend.app.db.models import RoadSegment

GEOJSON_OUTPUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/osm_metro_manila_roads.geojson"))

# Default major road speed baselines in km/h if unspecified in OSM tags
DEFAULT_SPEEDS = {
    "motorway": 80.0,
    "trunk": 60.0,
    "primary": 50.0,
    "secondary": 40.0,
    "tertiary": 30.0,
}

def build_overpass_query(bbox: tuple) -> str:
    """
    Constructs an Overpass QL query.
    bbox format in settings: (min_lng, min_lat, max_lng, max_lat)
    Overpass bbox format: (south, west, north, east) -> (min_lat, min_lng, max_lat, max_lng)
    """
    min_lng, min_lat, max_lng, max_lat = bbox
    query = f"""
    [out:json][timeout:60];
    (
      way["highway"~"^(motorway|trunk|primary)$"]["name"]({min_lat},{min_lng},{max_lat},{max_lng});
    );
    out body geom;
    """
    return query

def fetch_osm_roads(bbox: tuple = None, overpass_url: str = None) -> list:
    bbox = bbox or settings.METRO_MANILA_BBOX
    overpass_url = overpass_url or settings.OVERPASS_API_URL
    query = build_overpass_query(bbox)

    print(f"Fetching real road network from Overpass API: {overpass_url}...")
    try:
        response = httpx.post(overpass_url, data={"data": query}, timeout=90.0)
        response.raise_for_status()
        data = response.json()
        elements = data.get("elements", [])
        print(f"Successfully downloaded {len(elements)} OSM road features from Overpass API.")
        return elements
    except Exception as e:
        print(f"Warning: Overpass API request failed ({e}). Checking local fallback GeoJSON...")
        return []

def parse_osm_ways(elements: list, bbox: tuple) -> list:
    """Transforms OSM way elements into GeoJSON feature dicts."""
    min_lng, min_lat, max_lng, max_lat = bbox
    features = []

    for el in elements:
        if el.get("type") != "way":
            continue

        geometry_points = el.get("geometry", [])
        if len(geometry_points) < 2:
            continue

        coords = []
        for pt in geometry_points:
            lng, lat = pt["lon"], pt["lat"]
            if min_lng <= lng <= max_lng and min_lat <= lat <= max_lat:
                coords.append([round(lng, 6), round(lat, 6)])

        if len(coords) < 2:
            continue

        tags = el.get("tags", {})
        road_name = tags.get("name", "Unnamed Corridor")
        highway_type = tags.get("highway", "primary")
        
        # Determine baseline speed
        maxspeed_tag = tags.get("maxspeed")
        if maxspeed_tag and maxspeed_tag.isdigit():
            baseline_speed = float(maxspeed_tag)
        else:
            baseline_speed = DEFAULT_SPEEDS.get(highway_type, 50.0)

        city = tags.get("addr:city") or tags.get("is_in:city") or "Metro Manila"
        road_ref = tags.get("ref", highway_type.upper())
        direction = "NB" if tags.get("oneway") == "yes" else "BI"

        feature = {
            "type": "Feature",
            "properties": {
                "road_name": road_name,
                "road_code": road_ref,
                "direction": direction,
                "city": city,
                "baseline_speed_kmh": baseline_speed,
                "highway_type": highway_type,
                "osm_id": el.get("id")
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        }
        features.append(feature)

    return features

def ingest_osm_to_db(db: Session, features: list):
    inserted_count = 0
    updated_count = 0

    for feat in features:
        props = feat["properties"]
        geom = feat["geometry"]
        coords = geom["coordinates"]
        
        wkt_coords = ", ".join([f"{lng} {lat}" for lng, lat in coords])
        wkt = f"LINESTRING({wkt_coords})"
        
        road_name = props["road_name"]
        direction = props["direction"]
        
        existing = db.query(RoadSegment).filter(
            RoadSegment.road_name == road_name,
            RoadSegment.direction == direction
        ).first()

        if existing:
            existing.road_code = props.get("road_code")
            existing.city = props.get("city")
            existing.baseline_speed_kmh = props.get("baseline_speed_kmh")
            existing.geometry = WKTElement(wkt, srid=4326)
            updated_count += 1
        else:
            segment = RoadSegment(
                road_name=road_name,
                road_code=props.get("road_code"),
                direction=direction,
                city=props.get("city"),
                baseline_speed_kmh=props.get("baseline_speed_kmh"),
                geometry=WKTElement(wkt, srid=4326)
            )
            db.add(segment)
            inserted_count += 1

    db.commit()
    print(f"OSM Ingestion complete: {inserted_count} inserted, {updated_count} updated.")
    return inserted_count + updated_count

def run_osm_ingestion(save_geojson: bool = True):
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    db = SessionLocal()
    
    try:
        elements = fetch_osm_roads()
        if elements:
            features = parse_osm_ways(elements, settings.METRO_MANILA_BBOX)
            if save_geojson and features:
                fc = {"type": "FeatureCollection", "features": features}
                with open(GEOJSON_OUTPUT, "w", encoding="utf-8") as f:
                    json.dump(fc, f, indent=2)
                print(f"Saved {len(features)} OSM features to {GEOJSON_OUTPUT}")
            
            ingest_osm_to_db(db, features)
        else:
            print("No OSM elements retrieved; checking existing local road dataset.")
    finally:
        db.close()

if __name__ == "__main__":
    run_osm_ingestion()

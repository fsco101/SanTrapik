import os
import sys
from datetime import datetime, timedelta, timezone
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import get_session_local, get_engine
from backend.app.db.models import RoadSegment, Incident

SAMPLE_INCIDENTS = [
    {
      "segment_match": "EDSA - Ortigas Flyover to Shaw Boulevard",
      "incident_type": "ACCIDENT",
      "description": "2-vehicle collision occupying 2 middle lanes; traffic enforcers on scene",
      "severity": "CRITICAL",
      "status": "ACTIVE",
      "reported_minutes_ago": 28,
      "point_lng_lat": [121.0575, 14.5855],
      "data_source": "MMDA_METROBASE"
    },
    {
      "segment_match": "EDSA - Guadalupe to Buendia",
      "incident_type": "STALLED_VEHICLE",
      "description": "Stalled commuter bus occupying outer carousel lane near Estrella",
      "severity": "HIGH",
      "status": "CLEARING",
      "reported_minutes_ago": 45,
      "point_lng_lat": [121.0360, 14.5610],
      "data_source": "MMDA_TRAFFIC_ENFORCEMENT"
    },
    {
      "segment_match": "C-5 - Ortigas Junction to Bagong Ilog Flyover",
      "incident_type": "ROADWORK",
      "description": "DPWH concrete re-blocking and asphalt overlay; 1 lane passable",
      "severity": "HIGH",
      "status": "ACTIVE",
      "reported_minutes_ago": 120,
      "point_lng_lat": [121.0690, 14.5740],
      "data_source": "DPWH_NCR"
    },
    {
      "segment_match": "España Boulevard - Welcome Rotonda to UST",
      "incident_type": "FLOOD",
      "description": "Flash flooding gutter-deep due to localized heavy thunderstorm",
      "severity": "MEDIUM",
      "status": "ACTIVE",
      "reported_minutes_ago": 35,
      "point_lng_lat": [120.9920, 14.6120],
      "data_source": "MANILA_DRRMO"
    },
    {
      "segment_match": "Commonwealth - Batasan to Tandang Sora",
      "incident_type": "STALLED_VEHICLE",
      "description": "Stalled delivery truck causing slow movement near Ever Gotesco",
      "severity": "MEDIUM",
      "status": "ACTIVE",
      "reported_minutes_ago": 18,
      "point_lng_lat": [121.0850, 14.6710],
      "data_source": "QC_DPOS"
    },
    {
      "segment_match": "Marcos Highway - Marikina Riverbanks to Santolan",
      "incident_type": "ACCIDENT",
      "description": "Motorcycle-car sideswipe occupying leftmost lane westbound",
      "severity": "HIGH",
      "status": "ACTIVE",
      "reported_minutes_ago": 12,
      "point_lng_lat": [121.1010, 14.6255],
      "data_source": "PASIG_TPMO"
    },
    {
      "segment_match": "Roxas Boulevard - Luneta to CCP Complex",
      "incident_type": "ROADWORK",
      "description": "Baywalk barrier rehabilitation; minor slowdown on outermost lane",
      "severity": "LOW",
      "status": "ACTIVE",
      "reported_minutes_ago": 240,
      "point_lng_lat": [120.9835, 14.5620],
      "data_source": "DPWH_SOUTH_MANILA"
    },
    {
      "segment_match": "EDSA - Balintawak to Muñoz",
      "incident_type": "ACCIDENT",
      "description": "Overturned cargo vehicle; wrecker clearing operations completed",
      "severity": "MEDIUM",
      "status": "RESOLVED",
      "reported_minutes_ago": 180,
      "point_lng_lat": [121.0150, 14.6575],
      "data_source": "MMDA_METROBASE"
    }
]

def seed_incidents(db: Session):
    print("Seeding road incidents...")
    now = datetime.now(timezone.utc)
    created_count = 0

    for item in SAMPLE_INCIDENTS:
        # Find matching road segment
        segment = db.query(RoadSegment).filter(
            RoadSegment.road_name == item["segment_match"]
        ).first()

        lng, lat = item["point_lng_lat"]
        point_wkt = f"POINT({lng} {lat})"

        reported_time = now - timedelta(minutes=item["reported_minutes_ago"])
        cleared_time = now - timedelta(minutes=30) if item["status"] == "RESOLVED" else None

        incident = Incident(
            road_segment_id=segment.id if segment else None,
            incident_type=item["incident_type"],
            description=item["description"],
            severity=item["severity"],
            status=item["status"],
            geometry=WKTElement(point_wkt, srid=4326),
            reported_at=reported_time,
            cleared_at=cleared_time,
            data_source=item["data_source"]
        )
        db.add(incident)
        created_count += 1

    db.commit()
    print(f"Road incidents seeding complete: {created_count} incidents created.")
    return created_count

if __name__ == "__main__":
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    db = SessionLocal()
    try:
        seed_incidents(db)
    finally:
        db.close()

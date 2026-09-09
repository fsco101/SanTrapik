import os
import sys
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.db.session import get_session_local, get_engine
from backend.app.db.models import RoadSegment, TrafficRecord

def classify_traffic(speed: float, baseline: float):
    ratio = speed / baseline if baseline > 0 else 0
    if ratio >= 0.80:
        return "NORMAL", round((1.0 - ratio) * 100, 1)
    elif ratio >= 0.50:
        return "MODERATE", round((1.0 - ratio) * 100, 1)
    elif ratio >= 0.25:
        return "HEAVY", round((1.0 - ratio) * 100, 1)
    else:
        return "SEVERE", min(99.0, round((1.0 - ratio) * 100, 1))

def seed_traffic_records(db: Session, records_per_segment: int = 15):
    segments = db.query(RoadSegment).all()
    if not segments:
        print("No road segments found. Run ingest_roads.py first!")
        return 0

    print(f"Generating traffic telemetry for {len(segments)} road segments...")
    now = datetime.now(timezone.utc)
    total_records = 0

    # Known bottleneck segments to induce realistic severe traffic
    heavy_corridors = ["Ortigas Flyover", "Guadalupe", "Cubao", "Bagong Ilog", "Balintawak"]

    for seg in segments:
        baseline = float(seg.baseline_speed_kmh)
        is_bottleneck = any(h in seg.road_name for h in heavy_corridors)

        # 1. Generate historical records over past 48 hours
        for i in range(records_per_segment, 0, -1):
            obs_time = now - timedelta(hours=i * 2, minutes=random.randint(0, 30))
            hour = obs_time.hour
            is_rush_hour = (7 <= hour <= 10) or (17 <= hour <= 21)

            if is_bottleneck and is_rush_hour:
                speed = round(random.uniform(baseline * 0.12, baseline * 0.24), 1)  # SEVERE
            elif is_rush_hour:
                speed = round(random.uniform(baseline * 0.28, baseline * 0.48), 1)  # HEAVY
            elif 23 <= hour or hour <= 5:
                speed = round(random.uniform(baseline * 0.85, baseline * 1.05), 1)  # NORMAL
            else:
                speed = round(random.uniform(baseline * 0.55, baseline * 0.78), 1)  # MODERATE

            traffic_level, congestion_pct = classify_traffic(speed, baseline)

            record = TrafficRecord(
                road_segment_id=seg.id,
                traffic_level=traffic_level,
                average_speed_kmh=speed,
                congestion_percentage=max(0.0, congestion_pct),
                observed_at=obs_time,
                data_source="MMDA_CCTV_TELEMETRY"
            )
            db.add(record)
            total_records += 1

        # 2. Add current active telemetry (fresh within last 10 minutes)
        current_hour = now.hour
        is_current_rush = (7 <= current_hour <= 10) or (17 <= current_hour <= 21)
        if is_bottleneck:
            curr_speed = round(random.uniform(baseline * 0.15, baseline * 0.23), 1)  # SEVERE
        elif is_current_rush:
            curr_speed = round(random.uniform(baseline * 0.30, baseline * 0.45), 1)  # HEAVY
        else:
            curr_speed = round(random.uniform(baseline * 0.65, baseline * 0.85), 1)

        traffic_level, congestion_pct = classify_traffic(curr_speed, baseline)
        latest_record = TrafficRecord(
            road_segment_id=seg.id,
            traffic_level=traffic_level,
            average_speed_kmh=curr_speed,
            congestion_percentage=max(0.0, congestion_pct),
            observed_at=now - timedelta(minutes=random.randint(1, 5)),
            data_source="MMDA_LIVE_API"
        )
        db.add(latest_record)
        total_records += 1

    db.commit()
    print(f"Traffic telemetry seeding complete: {total_records} records created.")
    return total_records

if __name__ == "__main__":
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    db = SessionLocal()
    try:
        seed_traffic_records(db)
    finally:
        db.close()

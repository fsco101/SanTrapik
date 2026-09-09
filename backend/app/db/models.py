import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from backend.app.db.session import Base

class RoadSegment(Base):
    __tablename__ = "road_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    road_name = Column(String(128), nullable=False, index=True)
    road_code = Column(String(32), nullable=True)
    direction = Column(String(32), nullable=False)  # 'NB', 'SB', 'EB', 'WB', 'BOTH'
    city = Column(String(64), nullable=False, index=True)
    baseline_speed_kmh = Column(Numeric(5, 2), nullable=False)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    traffic_records = relationship("TrafficRecord", back_populates="road_segment", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="road_segment")
    predictions = relationship("Prediction", back_populates="road_segment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RoadSegment(name='{self.road_name}', dir='{self.direction}', city='{self.city}')>"


class TrafficRecord(Base):
    __tablename__ = "traffic_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    road_segment_id = Column(UUID(as_uuid=True), ForeignKey("road_segments.id", ondelete="CASCADE"), nullable=False, index=True)
    traffic_level = Column(String(16), nullable=False, index=True)  # 'NORMAL', 'MODERATE', 'HEAVY', 'SEVERE'
    average_speed_kmh = Column(Numeric(5, 2), nullable=False)
    congestion_percentage = Column(Numeric(5, 2), nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    data_source = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    road_segment = relationship("RoadSegment", back_populates="traffic_records")

    def __repr__(self):
        return f"<TrafficRecord(segment_id='{self.road_segment_id}', level='{self.traffic_level}', speed={self.average_speed_kmh})>"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    road_segment_id = Column(UUID(as_uuid=True), ForeignKey("road_segments.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_type = Column(String(64), nullable=False, index=True)  # 'ACCIDENT', 'ROADWORK', 'FLOOD', 'STALLED_VEHICLE'
    description = Column(Text, nullable=True)
    severity = Column(String(16), nullable=False)  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)  # 'REPORTED', 'ACTIVE', 'CLEARING', 'RESOLVED'
    geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False)
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    data_source = Column(String(64), nullable=False)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    road_segment = relationship("RoadSegment", back_populates="incidents")

    def __repr__(self):
        return f"<Incident(type='{self.incident_type}', severity='{self.severity}', status='{self.status}')>"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    road_segment_id = Column(UUID(as_uuid=True), ForeignKey("road_segments.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_relief_time = Column(DateTime(timezone=True), nullable=False)
    predicted_relief_minutes = Column(Integer, nullable=False)
    confidence_score = Column(Numeric(4, 3), nullable=False)
    model_version = Column(String(32), nullable=False)
    features_snapshot = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    road_segment = relationship("RoadSegment", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(segment_id='{self.road_segment_id}', relief_min={self.predicted_relief_minutes}, conf={self.confidence_score})>"


class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_name = Column(String(128), nullable=False)
    destination_name = Column(String(128), nullable=False)
    origin_geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    destination_geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    route_geom = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    distance_meters = Column(Numeric(10, 2), nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<Route(origin='{self.origin_name}', dest='{self.destination_name}')>"

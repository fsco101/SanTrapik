"""Initial PostGIS schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-09 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis";')

    # 2. road_segments
    op.create_table(
        'road_segments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('road_name', sa.String(128), nullable=False),
        sa.Column('road_code', sa.String(32), nullable=True),
        sa.Column('direction', sa.String(32), nullable=False),
        sa.Column('city', sa.String(64), nullable=False),
        sa.Column('baseline_speed_kmh', sa.Numeric(5, 2), nullable=False),
        sa.Column('geometry', Geometry(geometry_type='LINESTRING', srid=4326), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_road_segments_geom', 'road_segments', ['geometry'], postgresql_using='gist')
    op.create_index('idx_road_segments_road_name', 'road_segments', ['road_name'])
    op.create_index('idx_road_segments_city', 'road_segments', ['city'])

    # 3. traffic_records
    op.create_table(
        'traffic_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('road_segment_id', UUID(as_uuid=True), sa.ForeignKey('road_segments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('traffic_level', sa.String(16), nullable=False),
        sa.Column('average_speed_kmh', sa.Numeric(5, 2), nullable=False),
        sa.Column('congestion_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_source', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_traffic_records_segment_time', 'traffic_records', ['road_segment_id', sa.text('observed_at DESC')])
    op.create_index('idx_traffic_records_level', 'traffic_records', ['traffic_level'])

    # 4. incidents
    op.create_table(
        'incidents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('road_segment_id', UUID(as_uuid=True), sa.ForeignKey('road_segments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('incident_type', sa.String(64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='ACTIVE'),
        sa.Column('geometry', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cleared_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_source', sa.String(64), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_incidents_geom', 'incidents', ['geometry'], postgresql_using='gist')
    op.create_index('idx_incidents_status', 'incidents', ['status'])
    op.create_index('idx_incidents_type', 'incidents', ['incident_type'])

    # 5. predictions
    op.create_table(
        'predictions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('road_segment_id', UUID(as_uuid=True), sa.ForeignKey('road_segments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('predicted_relief_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('predicted_relief_minutes', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(4, 3), nullable=False),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('features_snapshot', JSONB(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_predictions_segment', 'predictions', ['road_segment_id', sa.text('generated_at DESC')])

    # 6. routes
    op.create_table(
        'routes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('origin_name', sa.String(128), nullable=False),
        sa.Column('destination_name', sa.String(128), nullable=False),
        sa.Column('origin_geom', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('destination_geom', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('route_geom', Geometry(geometry_type='LINESTRING', srid=4326), nullable=False),
        sa.Column('distance_meters', sa.Numeric(10, 2), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_routes_geom', 'routes', ['route_geom'], postgresql_using='gist')

def downgrade() -> None:
    op.drop_table('routes')
    op.drop_table('predictions')
    op.drop_table('incidents')
    op.drop_table('traffic_records')
    op.drop_table('road_segments')

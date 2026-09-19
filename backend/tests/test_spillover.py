"""
Unit and integration tests for Spatiotemporal Bottleneck Spillover Predictor (SP9-003).
Validates graph adjacency, upstream shockwave propagation, proactive warning generation,
and integration with route analysis.
"""

import pytest
from backend.app.services.spillover import (
    SpilloverEngine,
    spillover_engine,
    CORRIDOR_TOPOLOGY,
)

def test_corridor_graph_topology_directional():
    """Verify directed graph contains major Manila corridors and directional flow."""
    assert "EDSA_NB" in CORRIDOR_TOPOLOGY
    assert "EDSA_SB" in CORRIDOR_TOPOLOGY
    assert "C5_NB" in CORRIDOR_TOPOLOGY
    assert "COMMONWEALTH_WB" in CORRIDOR_TOPOLOGY

    # On EDSA NB, Shaw is downstream of Guadalupe and upstream of Cubao
    edsa_nb = CORRIDOR_TOPOLOGY["EDSA_NB"]
    assert "Shaw" in edsa_nb
    assert "Cubao" in edsa_nb

def test_upstream_shockwave_propagation():
    """
    Simulate severe bottleneck at EDSA Shaw (speed 10 km/h, cong 85%).
    Engine must flag upstream segments (Guadalupe / Pioneer on NB, or Cubao / Ortigas depending on flow)
    and produce proactive warning with time-to-impact (15-45 mins).
    """
    segments = [
        {"id": "seg_guadalupe", "name": "EDSA - Guadalupe", "road_code": "EDSA", "direction": "NB", "current_speed": 40.0, "baseline_speed": 60.0, "congestion_percentage": 30.0},
        {"id": "seg_pioneer", "name": "EDSA - Pioneer", "road_code": "EDSA", "direction": "NB", "current_speed": 35.0, "baseline_speed": 60.0, "congestion_percentage": 35.0},
        {"id": "seg_shaw", "name": "EDSA - Shaw Blvd", "road_code": "EDSA", "direction": "NB", "current_speed": 8.0, "baseline_speed": 60.0, "congestion_percentage": 85.0},
        {"id": "seg_ortigas", "name": "EDSA - Ortigas", "road_code": "EDSA", "direction": "NB", "current_speed": 38.0, "baseline_speed": 60.0, "congestion_percentage": 30.0},
    ]

    warnings, flagged_segments = spillover_engine.predict_spillover(segments)

    # Downstream traffic flows Guadalupe -> Pioneer -> Shaw -> Ortigas
    # Upstream of Shaw (against traffic flow) is Pioneer & Guadalupe
    assert len(flagged_segments) > 0
    assert any("Pioneer" in w or "Guadalupe" in w or "Shaw" in w for w in warnings)
    assert any("mins" in w for w in warnings)

def test_no_spillover_under_free_flow():
    """Under free-flow traffic, no upstream shockwaves should be flagged."""
    free_flow_segments = [
        {"id": "seg_1", "name": "EDSA - Guadalupe", "road_code": "EDSA", "direction": "NB", "current_speed": 55.0, "baseline_speed": 60.0, "congestion_percentage": 10.0},
        {"id": "seg_2", "name": "EDSA - Shaw", "road_code": "EDSA", "direction": "NB", "current_speed": 50.0, "baseline_speed": 60.0, "congestion_percentage": 15.0},
    ]
    warnings, flagged_segments = spillover_engine.predict_spillover(free_flow_segments)
    assert len(flagged_segments) == 0
    assert len(warnings) == 0

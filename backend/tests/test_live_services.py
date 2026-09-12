import pytest
from backend.app.services.live_traffic import live_traffic_service
from backend.app.services.live_incidents import live_incident_feed_service
from backend.app.core.config import settings

def test_live_traffic_service_fallback_without_keys():
    # When keys are empty, has_live_provider should be False and not error
    assert live_traffic_service.tomtom_key in (None, "")
    assert live_traffic_service.fetch_tomtom_flow_segment([121.05, 14.58]) is None

def test_live_incident_feed_service_ingestion():
    test_incident = {
        "lng": 121.055,
        "lat": 14.582,
        "incident_type": "ACCIDENT",
        "severity": "HIGH",
        "description": "Live crash report on EDSA",
        "data_source": "TEST_UNIT"
    }
    result = live_incident_feed_service.process_incident_report(test_incident)
    assert result["id"].startswith("inc_live_")
    assert result["status"] == "ACTIVE"
    assert result["severity"] == "HIGH"
    assert result["data_source"] == "TEST_UNIT"

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_places_search_known_landmark():
    resp = client.get("/api/v1/places/search?q=Makati")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "name" in first
    assert "lat" in first
    assert "lng" in first
    # Coordinates must be within Metro Manila bbox
    assert 14.35 <= first["lat"] <= 14.80
    assert 120.90 <= first["lng"] <= 121.15

def test_places_search_empty_query():
    resp = client.get("/api/v1/places/search?q=")
    # min_length=1 should return 422 validation error
    assert resp.status_code == 422

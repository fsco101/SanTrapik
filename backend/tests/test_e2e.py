import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_e2e_full_query_flow_to_prediction():
    """
    End-to-end integration test verifying the complete pipeline:
    User coordinates -> Routing Service -> Spatial Snapping -> ML Relief Prediction -> Route Comparison Recommendation.
    """
    start_time = time.perf_counter()
    
    # Origin: Quezon City Memorial Circle, Destination: Ayala Triangle Gardens, Makati
    payload = {
        "origin": {
            "lat": 14.6515,
            "lng": 121.0494,
            "name": "Quezon City Memorial Circle"
        },
        "destination": {
            "lat": 14.5573,
            "lng": 121.0234,
            "name": "Ayala Triangle Gardens, Makati"
        },
        "include_alternatives": True
    }
    
    response = client.post("/api/v1/route/analyze", json=payload)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    
    routes = data["data"]["routes"]
    assert len(routes) >= 2, "Expected at least primary and alternative routes"

    # Verify primary route structure
    primary = routes[0]
    assert primary["id"].startswith("rt_")
    assert primary["summary"]["total_distance_km"] > 0
    assert primary["summary"]["estimated_travel_time_min"] > 0
    assert "geometry" in primary
    assert primary["geometry"]["type"] == "LineString"
    assert len(primary["geometry"]["coordinates"]) >= 2

    # Verify ML relief prediction integration
    expected_relief = primary.get("expected_relief", {})
    assert expected_relief.get("is_predicted") is True
    assert 5 <= expected_relief.get("estimated_minutes_remaining") <= 180
    assert expected_relief.get("confidence") >= 0.50
    assert expected_relief.get("confidence_interval") is not None
    assert "model_version" in expected_relief
    assert "relief_time" in expected_relief

    # Verify Route Comparison recommendation engine
    assert any(r.get("is_recommended") is True for r in routes), "At least one route must be marked as recommended"
    rec_route = next(r for r in routes if r.get("is_recommended") is True)
    assert rec_route.get("recommendation_reason"), "Recommended route must provide justification"

    print(f"\n[E2E Flow] Complete pipeline verified in {elapsed_ms:.2f}ms")

def test_e2e_latency_benchmark_under_1200ms():
    """
    SP5-004 Acceptance Criteria:
    95th percentile route analysis response time is < 1200ms under simulated load.
    """
    latencies = []
    payload = {
        "origin": {"lat": 14.6515, "lng": 121.0494, "name": "QC Circle"},
        "destination": {"lat": 14.5573, "lng": 121.0234, "name": "Ayala Triangle"},
        "include_alternatives": True
    }

    # Run 5 iterations to benchmark latency
    for _ in range(5):
        t0 = time.perf_counter()
        res = client.post("/api/v1/route/analyze", json=payload)
        t1 = time.perf_counter()
        assert res.status_code == 200
        latencies.append((t1 - t0) * 1000)

    latencies.sort()
    p95_index = int(0.95 * len(latencies))
    p95_latency = latencies[min(p95_index, len(latencies) - 1)]

    print(f"\n[E2E Latency] p95 latency: {p95_latency:.2f}ms (Target: < 1200ms)")
    assert p95_latency < 1200.0, f"p95 latency {p95_latency:.2f}ms exceeded 1200ms SLA target"

def test_e2e_rate_limiting_headers_and_enforcement():
    """
    SP5-004 Acceptance Criteria:
    Rate limiting enforces max 60 requests/minute per IP on public endpoints.
    Verifies X-RateLimit headers and HTTP 429 response when limit exceeded.
    """
    test_ip = "192.168.99.100"
    headers = {"X-Forwarded-For": test_ip}

    # Verify rate limit headers on standard request to public endpoint
    res = client.get("/api/v1/dashboard/stats", headers=headers)
    assert res.status_code == 200
    assert "x-ratelimit-limit" in res.headers
    assert "x-ratelimit-remaining" in res.headers
    assert res.headers["x-ratelimit-limit"] == "60"

    # Make rapid requests from custom client IP to trigger 429
    status_codes = []
    hit_429 = False
    for _ in range(65):
        r = client.get("/api/v1/dashboard/stats", headers=headers)
        status_codes.append(r.status_code)
        if r.status_code == 429:
            hit_429 = True
            body = r.json()
            assert body["status"] == "error"
            assert "Rate limit exceeded" in body["detail"]
            assert "retry_after_seconds" in body
            assert r.headers.get("retry-after") == "60"
            break

    assert hit_429, f"Expected HTTP 429 after exceeding 60 req/min limit, got statuses: {set(status_codes)}"

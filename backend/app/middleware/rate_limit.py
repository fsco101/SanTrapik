"""
Sliding-Window Rate Limiting Middleware for SanTrapik API.
Protects computationally expensive PostGIS spatial routing and crowdsourced incident endpoints
against denial-of-service, automated scraping, and spam injection.
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.default_max_requests = max_requests_per_minute
        self.default_window_seconds = 60.0
        # Maps (client_ip, category) -> list of timestamp floats
        self.requests_by_ip: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self.exempt_prefixes = ("/docs", "/redoc", "/api/v1/openapi.json", "/api/v1/health", "/favicon.ico")

    def reset(self):
        """Clears rate limit history (used for unit/integration tests)."""
        self.requests_by_ip.clear()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Exempt documentation, root, options preflight, and health check endpoints
        if path == "/" or method == "OPTIONS" or any(path.startswith(prefix) for prefix in self.exempt_prefixes):
            return await call_next(request)

        # Extract client IP respecting standard reverse-proxy headers
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        now = time.time()

        # Category-based rate limiting
        category = "general"
        max_requests = self.default_max_requests
        window_seconds = self.default_window_seconds

        if path == "/api/v1/route/analyze" and method == "POST":
            category = "route_analyze"
            max_requests = 60
            window_seconds = 60.0  # 60 req / 1 min
        elif path == "/api/v1/incidents" and method == "POST":
            category = "incident_report"
            max_requests = 5
            window_seconds = 600.0  # 5 reports / 10 mins
        elif "/vote-clearance" in path and method == "POST":
            category = "clearance_vote"
            max_requests = 20
            window_seconds = 600.0  # 20 votes / 10 mins
        elif "/telemetry/stream" in path:
            if "/subscription" in path and method == "POST":
                # High-frequency viewport renegotiation during map pan/zoom gestures
                category = "telemetry_subscription"
                max_requests = 180
                window_seconds = 60.0  # 180 req / 1 min (3 per sec)
            elif method == "GET":
                category = "telemetry_stream"
                max_requests = 60
                window_seconds = 60.0

        key = (client_ip, category)
        window_start = now - window_seconds
        timestamps = self.requests_by_ip[key]
        valid_timestamps = [ts for ts in timestamps if ts > window_start]
        self.requests_by_ip[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            oldest = valid_timestamps[0]
            if category == "general":
                retry_after = 60
                detail_msg = f"Rate limit exceeded. Maximum {max_requests} requests per minute allowed."
                retry_header = "60"
            else:
                retry_after = max(1, int(oldest + window_seconds - now))
                detail_msg = f"Rate limit exceeded for {category}. Maximum {max_requests} requests per {max(1, int(window_seconds // 60))} minutes allowed."
                retry_header = str(retry_after)

            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "category": category,
                    "detail": detail_msg,
                    "retry_after_seconds": retry_after
                },
                headers={
                    "Retry-After": retry_header,
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0"
                },
            )

        self.requests_by_ip[key].append(now)
        response = await call_next(request)
        remaining = max(0, max_requests - len(self.requests_by_ip[key]))
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

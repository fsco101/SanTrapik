"""
Rate limiting middleware for SanTrapik API.
Enforces max 60 requests/minute per client IP on public intelligence endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.window_seconds = 60.0
        self.requests_by_ip: Dict[str, List[float]] = defaultdict(list)
        self.exempt_prefixes = ("/docs", "/redoc", "/api/v1/openapi.json", "/api/v1/health", "/favicon.ico")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Exempt documentation, root, and health check endpoints
        if path == "/" or any(path.startswith(prefix) for prefix in self.exempt_prefixes):
            return await call_next(request)

        # Extract client IP respecting standard reverse-proxy headers
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        now = time.time()

        # Clean old timestamps outside sliding window
        window_start = now - self.window_seconds
        timestamps = self.requests_by_ip[client_ip]
        self.requests_by_ip[client_ip] = [ts for ts in timestamps if ts > window_start]

        if len(self.requests_by_ip[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "detail": f"Rate limit exceeded. Maximum {self.max_requests} requests per minute allowed.",
                    "retry_after_seconds": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0"
                },
            )

        self.requests_by_ip[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(self.requests_by_ip[client_ip])))
        return response

import time
import uuid
import logging
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("avom.access")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies industry-standard OWASP security headers to all HTTP responses.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Injects unique correlation X-Request-ID and tracks request execution latency.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        # Exclude high-frequency health probes from verbose logging
        if not request.url.path.startswith("/health") and not request.url.path.endswith("/readiness"):
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration_ms}ms"
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Zero-dependency in-memory sliding token bucket rate limiter per client IP.
    """
    def __init__(self, app, max_requests: int = 180, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # client_ip -> (last_reset_timestamp, request_count)
        self._clients: Dict[str, Tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Bypass rate limiter for health checks
        if request.url.path in ("/health", "/api/v1/health", "/api/v1/health/readiness"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        last_time, count = self._clients.get(client_ip, (now, 0))

        if now - last_time > self.window_seconds:
            self._clients[client_ip] = (now, 1)
        else:
            if count >= self.max_requests:
                retry_after = int(self.window_seconds - (now - last_time)) + 1
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please slow down.", "retry_after_seconds": retry_after},
                    headers={"Retry-After": str(retry_after)}
                )
            self._clients[client_ip] = (last_time, count + 1)

        return await call_next(request)

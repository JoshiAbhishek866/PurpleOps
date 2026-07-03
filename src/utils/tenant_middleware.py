"""
Tenant-Scoping Middleware for PurpleOps

Extracts tenant_id from JWT claims and injects it into the request state,
ensuring all downstream operations are scoped to the correct tenant.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from src.config import Config
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant_id from JWT and adds it to request.state.

    Public endpoints (health, root, auth) are excluded.
    """

    # Paths that don't require tenant context
    EXCLUDED_PREFIXES = (
        "/health", "/api/health", "/docs", "/openapi.json", "/redoc",
        "/api/auth/", "/api/admin/auth/",
    )

    async def dispatch(self, request: Request, call_next):
        # Skip public endpoints
        path = request.url.path
        if path == "/" or any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return await call_next(request)

        # Extract tenant_id from JWT if present
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                # Try client JWT first, then admin JWT
                try:
                    payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
                except JWTError:
                    payload = jwt.decode(token, Config.ADMIN_JWT_SECRET, algorithms=["HS256"])

                request.state.tenant_id = payload.get("tenant_id", "default")
                request.state.user_id = payload.get("userId") or payload.get("user_id")
                request.state.user_role = payload.get("role", "viewer")
            except JWTError:
                # Auth middleware will handle the 401
                request.state.tenant_id = None
                request.state.user_id = None
                request.state.user_role = None
        else:
            request.state.tenant_id = None
            request.state.user_id = None
            request.state.user_role = None

        return await call_next(request)

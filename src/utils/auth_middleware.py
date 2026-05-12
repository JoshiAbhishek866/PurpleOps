"""
Authentication Middleware for Sentinel AI
Reusable FastAPI dependencies for protecting endpoints.
"""

from fastapi import Request, HTTPException, Depends
from jose import jwt, ExpiredSignatureError, JWTError
from typing import Optional, List
from src.config import Config


def _extract_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    return auth_header.replace("Bearer ", "")


async def require_auth(request: Request) -> dict:
    """
    FastAPI dependency: require a valid client JWT.
    Returns the decoded payload (contains userId, exp).
    """
    token = _extract_token(request)
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_admin(request: Request) -> dict:
    """
    FastAPI dependency: require a valid admin JWT.
    Returns the decoded payload (contains user_id, email, exp).
    """
    token = _extract_token(request)
    try:
        payload = jwt.decode(token, Config.ADMIN_JWT_SECRET, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(allowed_roles: List[str]):
    """
    Factory: returns a dependency that checks the user's role.
    Usage: Depends(require_role(["org_admin", "analyst"]))
    """
    async def _check_role(request: Request) -> dict:
        payload = await require_auth(request)

        # Lookup user role from DB
        db = getattr(request.app.state, "db", None)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")

        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(payload["userId"])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        role = user.get("role", "viewer")
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        payload["role"] = role
        return payload

    return _check_role

"""
Tenant Model for Sentinel AI Multi-Tenancy

Defines the data structures for tenant isolation.
Each organization gets a tenant_id that scopes all data.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class Tenant(BaseModel):
    """Represents an organization using the platform."""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Organization name")
    allowed_targets: List[str] = Field(
        default_factory=list,
        description="Allowlisted scan targets (domains, IPs, CIDRs)"
    )
    config: Dict = Field(
        default_factory=dict,
        description="Tenant-specific configuration overrides"
    )
    max_concurrent_scans: int = Field(default=5, description="Max simultaneous scans")
    is_active: bool = Field(default=True, description="Whether the tenant is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TenantUser(BaseModel):
    """Maps a user to a tenant with a role."""
    user_id: str
    tenant_id: str
    role: str = Field(
        default="viewer",
        description="One of: org_admin, analyst, viewer"
    )
    is_active: bool = True


# Role hierarchy for RBAC checks
ROLE_HIERARCHY = {
    "org_admin": 3,   # Full access: manage users, configs, run all scans
    "analyst": 2,     # Run scans, view results, manage campaigns
    "viewer": 1,      # Read-only: view results and dashboards
}


def has_permission(user_role: str, required_role: str) -> bool:
    """Check if user_role has at least the privileges of required_role."""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)

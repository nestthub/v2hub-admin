"""
Pydantic models for Admin API endpoints.

Admin-specific models for user management, IP bans, and whitelist operations.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    # IP Ban Management
    "IPBanEntry",
    "IPBanListResponse",
    "IPBanRequest",
    "IPBanStatusResponse",
    "IPUnbanRequest",
    "IPUnbanResponse",
    # Tonen Management
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    # User Management
    "UserCreateRequest",
    "UserCreateResponse",
    "UserResponse",
    "UserStatusUpdateRequest",
    # Whitelist Management
    "WhitelistAddRequest",
    "WhitelistAddResponse",
    "WhitelistEntry",
    "WhitelistListResponse",
    "WhitelistRemoveRequest",
    "WhitelistRemoveResponse",
]


class AdminBaseModel(BaseModel):
    """Base model for admin endpoints."""

    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════


class UserCreateRequest(AdminBaseModel):
    """Request model for creating a new user."""

    user_id: int = Field(..., description="External user ID", gt=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 12345,
            }
        }
    )


class UserResponse(AdminBaseModel):
    """Response model for user."""

    user_hash: str = Field(..., description="Generated user hash")
    user_id: int = Field(..., description="User ID")
    api_token: str = Field(..., description="Generated API token")
    is_active: bool = Field(..., description="Account status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_hash": "a1b2c3d4e5f6...",
                "user_id": 12345,
                "api_token": "12345:a1b2c3d4e5f6...",
                "is_active": True,
            }
        }
    )


class UserStatusUpdateRequest(AdminBaseModel):
    is_active: bool


class UserCreateResponse(UserResponse):
    """Response model for user creation."""

    pass


class TokenRefreshRequest(AdminBaseModel):
    """Request model for refreshing user token."""

    user_id: int = Field(..., description="User ID", gt=0)

    model_config = ConfigDict(json_schema_extra={"example": {"user_id": 12345}})


class TokenRefreshResponse(AdminBaseModel):
    """Response model for token refresh."""

    user_id: int = Field(..., description="User ID")
    new_api_token: str = Field(..., description="New API token")

    model_config = ConfigDict(
        json_schema_extra={"example": {"user_id": 12345, "new_api_token": "12345_x9y8z7w6v5u4..."}}
    )


class IPBanRequest(AdminBaseModel):
    """Request model for banning an IP."""

    ip_address: str = Field(..., description="IP address to ban")
    duration_seconds: int | None = Field(
        default=None, description="Ban duration in seconds (default: use system setting)"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"ip_address": "192.168.1.100", "duration_seconds": 3600}}
    )


class IPUnbanRequest(AdminBaseModel):
    """Request model for unbanning an IP."""

    ip_address: Annotated[str, Field(description="IP address to unban", min_length=8)]

    model_config = ConfigDict(json_schema_extra={"example": {"ip_address": "192.168.1.100"}})


class IPUnbanResponse(AdminBaseModel):
    """Response from unban operation."""

    ip_address: Annotated[str, Field(description="IP address")]
    was_banned: Annotated[bool, Field(description="Whether IP was previously banned")]
    message: Annotated[str, Field(description="Result message")]


class IPBanStatusResponse(AdminBaseModel):
    """Response model for ban status."""

    ip_address: Annotated[str, Field(description="Banned IP address")]
    is_banned: Annotated[bool, Field(description="Whether IP is now banned")]
    banned_until: Annotated[str | None, Field(None, description="Ban expiration time")]
    remaining_seconds: Annotated[int | None, Field(None, description="Seconds until unban", ge=0)]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ip_address": "192.168.1.100",
                "is_banned": True,
                "banned_until": "2026-04-20T12:00:00",
                "remaining_seconds": 3600,
            }
        }
    )


class IPBanEntry(AdminBaseModel):
    """Banlist entry model."""

    ip_address: Annotated[str, Field(description="Banned IP address")]
    banned_until: Annotated[str | None, Field(description="Ban expiration time")] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"ip_address": "192.168.1.100", "banned_until": "2026-04-20T10:00:00"}
        }
    )


class IPBanListResponse(AdminBaseModel):
    """Response model for banlist listing."""

    entries: list[IPBanEntry]
    total: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entries": [{"ip_address": "192.168.1.100", "banned_until": "2026-04-20T10:00:00"}],
                "total": 1,
            }
        }
    )


class WhitelistAddRequest(AdminBaseModel):
    """Request model for adding IP to whitelist."""

    ip_address: str = Field(..., description="IP address or CIDR to whitelist")
    description: str | None = Field(
        None, max_length=255, description="Description/reason for whitelisting"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"ip_address": "10.0.0.0/24", "description": "Internal office network"}
        }
    )


class WhitelistAddResponse(AdminBaseModel):
    """Response from whitelist add operation."""

    ip_address: Annotated[str, Field(description="Whitelisted IP/CIDR")]
    description: Annotated[str | None, Field(None, description="Description")]
    message: Annotated[str, Field(description="Result message")]


class WhitelistRemoveRequest(AdminBaseModel):
    """Request model for removing IP from whitelist."""

    ip_address: str = Field(..., description="IP address to remove")

    model_config = ConfigDict(json_schema_extra={"example": {"ip_address": "10.0.0.0/24"}})


class WhitelistRemoveResponse(AdminBaseModel):
    """Response from whitelist remove operation."""

    ip_address: Annotated[str, Field(description="IP address")]
    was_whitelisted: Annotated[bool, Field(description="Whether IP was previously whitelisted")]
    message: Annotated[str, Field(description="Result message")]


class WhitelistEntry(AdminBaseModel):
    """Whitelist entry model."""

    ip_address: str
    description: str | None = None
    added_at: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ip_address": "10.0.0.0/24",
                "description": "Internal office network",
                "added_at": "2026-04-20T10:00:00",
            }
        }
    )


class WhitelistListResponse(AdminBaseModel):
    """Response model for whitelist listing."""

    entries: Annotated[
        list[WhitelistEntry],
        Field(default_factory=list, description="List of whitelisted IPs"),
    ]
    total: Annotated[int, Field(description="Total number of entries", ge=0)]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entries": [
                    {
                        "ip_address": "10.0.0.0/24",
                        "description": "Internal office network",
                        "added_at": "2026-04-20T10:00:00",
                    }
                ],
                "total": 1,
            }
        }
    )

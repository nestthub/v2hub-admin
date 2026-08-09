"""
Pydantic models for Admin API.
"""

from .access_lists import (
    IPBanEntry,
    IPBanListResponse,
    IPBanRequest,
    IPBanStatusResponse,
    IPUnbanRequest,
    IPUnbanResponse,
    WhitelistAddRequest,
    WhitelistAddResponse,
    WhitelistEntry,
    WhitelistListResponse,
    WhitelistRemoveRequest,
    WhitelistRemoveResponse,
)
from .providers import (
    AllProvidersResponse,
    ProviderCreateRequest,
    ProviderCreateResponse,
    ProviderNameUpdateRequest,
    ProviderResponse,
    ProviderStatusUpdateRequest,
    ProviderTokenRefreshRequest,
    ProviderTokenRefreshResponse,
    ProviderURLUpdateRequest,
)
from .users import (
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserResponse,
    UserStatusUpdateRequest,
)

__all__ = [
    # Provider management
    "AllProvidersResponse",
    # IP ban management
    "IPBanEntry",
    "IPBanListResponse",
    "IPBanRequest",
    "IPBanStatusResponse",
    "IPUnbanRequest",
    "IPUnbanResponse",
    "ProviderCreateRequest",
    "ProviderCreateResponse",
    "ProviderNameUpdateRequest",
    "ProviderResponse",
    "ProviderStatusUpdateRequest",
    "ProviderTokenRefreshRequest",
    "ProviderTokenRefreshResponse",
    "ProviderURLUpdateRequest",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    # User management
    "UserCreateRequest",
    "UserCreateResponse",
    "UserResponse",
    "UserStatusUpdateRequest",
    # Whitelist management
    "WhitelistAddRequest",
    "WhitelistAddResponse",
    "WhitelistEntry",
    "WhitelistListResponse",
    "WhitelistRemoveRequest",
    "WhitelistRemoveResponse",
]

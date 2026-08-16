"""
Asynchronous Admin API client.

Production-grade async client for VPN Subscription API admin endpoints.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlencode

from v2hub import __api_version__
from v2hub.core.retry import RetryConfig, with_async_retry
from v2hub.http.client import HTTPClient

from .auth import AdminAuthenticator
from .models import (
    AllProvidersResponse,
    IPBanListResponse,
    IPBanRequest,
    IPBanStatusResponse,
    IPUnbanRequest,
    IPUnbanResponse,
    ProviderCreateRequest,
    ProviderCreateResponse,
    ProviderNameUpdateRequest,
    ProviderResponse,
    ProviderStatusUpdateRequest,
    ProviderTokenRefreshRequest,
    ProviderTokenRefreshResponse,
    ProviderURLUpdateRequest,
    StatsResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserResponse,
    UserStatusUpdateRequest,
    WhitelistAddRequest,
    WhitelistAddResponse,
    WhitelistListResponse,
    WhitelistRemoveRequest,
    WhitelistRemoveResponse,
)

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = ["AsyncAdminClient"]


# ═══════════════════════════════════════════════════════════════════════════
# Async Admin Client
# ═══════════════════════════════════════════════════════════════════════════


class AsyncAdminClient:
    """
    Asynchronous Admin API client.

    Production-grade admin client with:
    - HMAC-SHA256 signature authentication
    - Automatic retries with exponential backoff
    - Pydantic models with validation
    - Comprehensive error handling
    - Request/response logging

    Example:
        async with AsyncAdminClient(
            base_url="https://api.example.com",
            secret_key="admin-secret-key"
        ) as client:
            # Create user
            user = await client.create_user(user_id=12345)
            print(f"Created user: {user.api_token}")

            # Ban IP
            ban = await client.ban_ip("192.168.1.100", duration_seconds=3600)
            print(f"Banned until: {ban.banned_until}")

            # Add to whitelist
            await client.add_to_whitelist("10.0.0.0/24", "Office network")
    """

    def __init__(
        self,
        base_url: str,
        secret_key: str,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """
        Initialize async admin API client.
        Args:
            base_url: API base URL (e.g., "https://api.example.com")
            secret_key: Admin secret key for HMAC authentication
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
        """
        self.base_url = base_url
        self.secret_key = secret_key
        self.retry_config = retry_config or RetryConfig()

        # Initialize authenticator
        self._authenticator = AdminAuthenticator(secret_key)

        # Initialize HTTP client (without default headers - we'll add them per request)
        self._http_client = HTTPClient(
            base_url=base_url,
            headers={},  # Headers added per-request with signature
            timeout=timeout,
        )

    async def __aenter__(self) -> AsyncAdminClient:
        """Async context manager entry."""
        await self._http_client.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self._http_client.close()

    async def connect(self) -> None:
        """Initialize HTTP client connection."""
        await self._http_client.connect()

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._http_client.close()

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to admin API.

        Args:
            method: HTTP method
            path: Request path
            data: Request body data (will be JSON-encoded)
            params: Query parameters

        Returns:
            Response data as dictionary
        """

        if params:
            query = urlencode({key: value for key, value in params.items() if value is not None})
            path = f"{path}?{query}"

        body = json.dumps(data) if data else ""

        auth_headers = self._authenticator.sign_request(
            method,
            path,
            body,
        )

        response = await self._http_client.request(
            method=method,
            path=path,
            headers=auth_headers,
            content=body.encode("utf-8") if body else None,
        )

        return response.json() if response.content else {}

    # ═══════════════════════════════════════════════════════════════════════
    # User Management
    # ═══════════════════════════════════════════════════════════════════════

    @with_async_retry()
    async def create_user(self, user_id: int) -> UserCreateResponse:
        """
        Create new user account.

        Args:
            user_id: External user ID (must be positive)
        Returns:
            User data with generated API token
        Raises:
            ValidationError: Invalid user_id
            ConflictError: User already exists
            AuthenticationError: Invalid admin secret key
        Example:
            user = await client.create_user(user_id=12345)
            print(f"API Token: {user.api_token}")
            print(f"User Hash: {user.user_hash}")
        """
        request = UserCreateRequest(user_id=user_id)
        response = await self._request(
            "POST",
            f"/api/{__api_version__}/admin/users",
            request.model_dump(mode="json"),
        )
        return UserCreateResponse(**response)

    @with_async_retry()
    async def get_user(self, user_id: int) -> UserResponse:
        """
        Get user info.
        Args:
            user_id: External user ID
        Returns:
            User data
        Raises:
            NotFoundError: User not found
            AuthenticationError: Invalid admin secret key
        """
        response = await self._request(
            "GET",
            f"/api/{__api_version__}/admin/users/{user_id}",
        )
        return UserResponse(**response)

    @with_async_retry()
    async def delete_user(self, user_id: int) -> None:
        """
        Delete user account.
        Args:
            user_id: External user ID
        Raises:
            NotFoundError: User not found
            AuthenticationError: Invalid admin secret key
        """
        await self._request(
            "DELETE",
            f"/api/{__api_version__}/admin/users/{user_id}",
        )

    @with_async_retry()
    async def set_user_status(
        self,
        user_id: int,
        is_active: bool,
    ) -> UserResponse:
        """
        Update user active status.
        Args:
            user_id: External user ID
            is_active: True to activate, False to deactivate
        Returns:
            Updated user data
        Raises:
            NotFoundError: User not found
            AuthenticationError: Invalid admin secret key
        """

        request = UserStatusUpdateRequest(is_active=is_active)
        response = await self._request(
            "PATCH",
            f"/api/{__api_version__}/admin/users/{user_id}/status",
            request.model_dump(mode="json"),
        )
        return UserResponse(**response)

    @with_async_retry()
    async def refresh_token(self, user_id: int) -> TokenRefreshResponse:
        """
        Refresh user's API token.
        Args:
            user_id: User ID
        Returns:
            New token data
        Raises:
            NotFoundError: User not found
            AuthenticationError: Invalid admin secret key
        Example:
            result = await client.refresh_token(user_id=12345)
            print(f"New token: {result.new_api_token}")
        """
        request = TokenRefreshRequest(user_id=user_id)
        response = await self._request(
            "POST",
            f"/api/{__api_version__}/admin/users/refresh-token",
            request.model_dump(mode="json"),
        )
        return TokenRefreshResponse(**response)

    # ═══════════════════════════════════════════════════════════════════════
    # Provider Management
    # ═══════════════════════════════════════════════════════════════════════

    @with_async_retry()
    async def get_providers(self) -> AllProvidersResponse:
        """
        Get all providers.

        Returns:
            Mapping of provider names to provider hashes.

        Raises:
            AuthenticationError: Invalid admin secret key.

        Example:
            providers = await client.get_providers()
            for name, provider_hash in providers.provider_hashes.items():
                print(f"{name}: {provider_hash}")
        """
        response = await self._request(
            "GET",
            f"/api/{__api_version__}/admin/providers",
        )
        return AllProvidersResponse(**response)

    @with_async_retry()
    async def create_provider(
        self,
        owner_hash: str,
        provider_name: str,
        provider_url: str | None = None,
    ) -> ProviderCreateResponse:
        """
        Create a new provider account.

        Args:
            owner_hash: Hash of the user who owns the provider.
            provider_name: Unique provider name.
            provider_url: Optional provider website or bot URL.

        Returns:
            Created provider data with generated API token.

        Raises:
            ValidationError: Invalid request data.
            ConflictError: Provider name or owner already exists.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = await client.create_provider(
                owner_hash="a1b2c3d4e5f6...",
                provider_name="vpn123",
                provider_url="https://t.me/examplebot",
            )
            print(f"Provider hash: {provider.provider_hash}")
            print(f"API token: {provider.api_token}")
        """
        request = ProviderCreateRequest(
            owner_hash=owner_hash,
            provider_name=provider_name,
            provider_url=provider_url,
        )
        response = await self._request(
            "POST",
            f"/api/{__api_version__}/admin/providers",
            request.model_dump(mode="json", exclude_none=True),
        )
        return ProviderCreateResponse(**response)

    @with_async_retry()
    async def get_provider(self, provider_hash: str) -> ProviderResponse:
        """
        Get provider information.

        Args:
            provider_hash: Provider hash.

        Returns:
            Provider data including API token and account status.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = await client.get_provider(
                provider_hash="a1b2c3d4e5f6..."
            )
            print(provider.provider_name)
        """
        response = await self._request(
            "GET",
            f"/api/{__api_version__}/admin/providers/{provider_hash}",
        )
        return ProviderResponse(**response)

    @with_async_retry()
    async def delete_provider(self, provider_hash: str) -> None:
        """
        Delete a provider account.

        Deleting a provider also removes provider-owned data according
        to the API/database cascade rules.

        Args:
            provider_hash: Provider hash.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            await client.delete_provider(
                provider_hash="a1b2c3d4e5f6..."
            )
        """
        await self._request(
            "DELETE",
            f"/api/{__api_version__}/admin/providers/{provider_hash}",
        )

    @with_async_retry()
    async def set_provider_status(
        self,
        provider_hash: str,
        is_active: bool,
    ) -> ProviderResponse:
        """
        Update provider active status.

        Args:
            provider_hash: Provider hash.
            is_active: True to activate, False to deactivate.

        Returns:
            Updated provider data.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = await client.set_provider_status(
                provider_hash="a1b2c3d4e5f6...",
                is_active=False,
            )
            print(provider.is_active)
        """
        request = ProviderStatusUpdateRequest(
            is_active=is_active,
        )
        response = await self._request(
            "PATCH",
            f"/api/{__api_version__}/admin/providers/{provider_hash}/status",
            request.model_dump(mode="json"),
        )
        return ProviderResponse(**response)

    @with_async_retry()
    async def update_provider_url(
        self,
        provider_hash: str,
        provider_url: str | None,
    ) -> ProviderResponse:
        """
        Update provider URL.

        Args:
            provider_hash: Provider hash.
            provider_url: New provider URL. Pass None to remove the URL.

        Returns:
            Updated provider data.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = await client.update_provider_url(
                provider_hash="a1b2c3d4e5f6...",
                provider_url="https://t.me/examplebot",
            )
        """
        request = ProviderURLUpdateRequest(
            provider_url=provider_url,
        )
        response = await self._request(
            "PATCH",
            f"/api/{__api_version__}/admin/providers/{provider_hash}/url",
            request.model_dump(mode="json"),
        )
        return ProviderResponse(**response)

    @with_async_retry()
    async def update_provider_name(
        self,
        provider_hash: str,
        provider_name: str,
    ) -> ProviderResponse:
        """
        Update provider name.

        Args:
            provider_hash: Provider hash.
            provider_name: New provider name.

        Returns:
            Updated provider data.

        Raises:
            NotFoundError: Provider not found.
            ConflictError: Provider name is already in use.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = await client.update_provider_name(
                provider_hash="a1b2c3d4e5f6...",
                provider_name="new-vpn-provider",
            )
            print(provider.provider_name)
        """
        request = ProviderNameUpdateRequest(
            provider_name=provider_name,
        )
        response = await self._request(
            "PATCH",
            f"/api/{__api_version__}/admin/providers/{provider_hash}/name",
            request.model_dump(mode="json"),
        )
        return ProviderResponse(**response)

    @with_async_retry()
    async def refresh_provider_token(
        self,
        provider_hash: str,
    ) -> ProviderTokenRefreshResponse:
        """
        Refresh provider API token.

        The old token is invalidated and a new unique token is generated.

        Args:
            provider_hash: Provider hash.

        Returns:
            New provider API token.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            result = await client.refresh_provider_token(
                provider_hash="a1b2c3d4e5f6..."
            )
            print(f"New token: {result.new_api_token}")
        """
        request = ProviderTokenRefreshRequest(
            provider_hash=provider_hash,
        )
        response = await self._request(
            "POST",
            f"/api/{__api_version__}/admin/providers/refresh-token",
            request.model_dump(mode="json"),
        )
        return ProviderTokenRefreshResponse(**response)

    # ═══════════════════════════════════════════════════════════════════════
    # IP Ban Management
    # ═══════════════════════════════════════════════════════════════════════

    @with_async_retry()
    async def ban_ip(
        self,
        ip_address: str,
        duration_seconds: int | None = None,
    ) -> IPBanStatusResponse:
        """
        Ban IP address.
        Args:
            ip_address: IP address to ban
            duration_seconds: Ban duration in seconds (optional, uses default if not specified)
        Returns:
            Ban status with expiration time
        Raises:
            ValidationError: Invalid IP address
            AuthenticationError: Invalid admin secret key
        Example:
            # Ban for 1 hour
            ban = await client.ban_ip("192.168.1.100", duration_seconds=3600)
            print(f"Banned until: {ban.banned_until}")
            print(f"Remaining: {ban.remaining_seconds}s")

            # Ban with default duration
            ban = await client.ban_ip("192.168.1.100")
        """
        request = IPBanRequest(
            ip_address=ip_address,
            duration_seconds=duration_seconds,
        )
        response = await self._request(
            "POST",
            f"/api/{__api_version__}/admin/bans",
            request.model_dump(mode="json", exclude_none=True),
        )
        return IPBanStatusResponse(**response)

    @with_async_retry()
    async def unban_ip(self, ip_address: str) -> IPUnbanResponse:
        """
        Unban IP address.
        Args:
            ip_address: IP address to unban
        Returns:
            Unban result
        Raises:
            AuthenticationError: Invalid admin secret key
        Example:
            result = await client.unban_ip("192.168.1.100")
            if result.was_banned:
                print(f"Unbanned {result.ip_address}")
            else:
                print(f"{result.ip_address} was not banned")
        """
        request = IPUnbanRequest(ip_address=ip_address)
        response = await self._request(
            "DELETE",
            f"/api/{__api_version__}/admin/bans",
            request.model_dump(mode="json"),
        )
        return IPUnbanResponse(**response)

    @with_async_retry()
    async def get_ban_status(self, ip_address: str) -> IPBanStatusResponse:
        """
        Check IP ban status.
        Args:
            ip_address: IP address to check
        Returns:
            Ban status
        Raises:
            AuthenticationError: Invalid admin secret key
        Example:
            status = await client.get_ban_status("192.168.1.100")
            if status.is_banned:
                print(f"Banned until: {status.banned_until}")
                print(f"Remaining: {status.remaining_seconds}s")
            else:
                print("Not banned")
        """
        response = await self._request(
            "GET",
            f"/api/{__api_version__}/admin/bans/{ip_address}",
        )
        return IPBanStatusResponse(**response)

    @with_async_retry()
    async def get_ban_list(self) -> IPBanListResponse:
        """
        Get all banned IPs.
        Returns:
            List of all bans
        Raises:
            AuthenticationError: Invalid admin secret key
        Example:
            bans = await client.get_ban_list()
            print(f"Total bans: {bans.total}")
            for ban in bans.entries:
                print(f"  {ban.ip_address} until {ban.banned_until}")
        """
        response = await self._request("GET", f"/api/{__api_version__}/admin/bans")
        return IPBanListResponse(**response)

    # ═══════════════════════════════════════════════════════════════════════
    # Whitelist Management
    # ═══════════════════════════════════════════════════════════════════════

    @with_async_retry()
    async def add_to_whitelist(
        self,
        ip_address: str,
        description: str | None = None,
    ) -> WhitelistAddResponse:
        """
        Add IP to whitelist.
        Args:
            ip_address: IP address or CIDR to whitelist
            description: Optional description
        Returns:
            Whitelist add result
        Raises:
            ValidationError: Invalid IP address/CIDR
            AuthenticationError: Invalid admin secret key
        Example:
            result = await client.add_to_whitelist(
                "10.0.0.0/24",
                description="Office network"
            )
            print(result.message)
        """
        request = WhitelistAddRequest(
            ip_address=ip_address,
            description=description,
        )
        response = await self._request(
            "POST",
            f"/api/{__api_version__}/admin/whitelist",
            request.model_dump(mode="json", exclude_none=True),
        )
        return WhitelistAddResponse(**response)

    @with_async_retry()
    async def remove_from_whitelist(self, ip_address: str) -> WhitelistRemoveResponse:
        """
        Remove IP from whitelist.
        Args:
            ip_address: IP address to remove
        Returns:
            Whitelist remove result
        Raises:
            AuthenticationError: Invalid admin secret key
        Example:
            result = await client.remove_from_whitelist("10.0.0.0/24")
            if result.was_whitelisted:
                print(f"Removed {result.ip_address} from whitelist")
            else:
                print(f"{result.ip_address} was not whitelisted")
        """
        request = WhitelistRemoveRequest(ip_address=ip_address)
        response = await self._request(
            "DELETE",
            f"/api/{__api_version__}/admin/whitelist",
            request.model_dump(mode="json"),
        )
        return WhitelistRemoveResponse(**response)

    @with_async_retry()
    async def list_whitelist(self) -> WhitelistListResponse:
        """
        Get all whitelisted IPs.
        Returns:
            List of all whitelist entries
        Raises:
            AuthenticationError: Invalid admin secret key
        Example:
            whitelist = await client.list_whitelist()
            print(f"Total entries: {whitelist.total}")
            for entry in whitelist.entries:
                print(f"  {entry.ip_address}: {entry.description}")
                print(f"    Added: {entry.added_at}")
        """
        response = await self._request("GET", f"/api/{__api_version__}/admin/whitelist")
        return WhitelistListResponse(**response)

    @with_async_retry()
    async def get_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period: Literal["day", "week", "month"] | None = None,
    ) -> StatsResponse:
        """
        Get API usage statistics.

        Args:
            start_date: Optional start date (ISO 8601).
            end_date: Optional end date (ISO 8601).
            period: Optional predefined period: day, week, or month.

        Returns:
            Aggregated API usage statistics.
        """
        params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "period": period,
        }

        response = await self._request(
            "GET",
            f"/api/{__api_version__}/admin/stats",
            params=params,
        )

        return StatsResponse(**response)

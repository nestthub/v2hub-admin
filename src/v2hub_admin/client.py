"""
Synchronous VPN Subscription API client.

Sync wrapper with proper event loop management.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TypeVar

from .async_client import AsyncAdminClient

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from v2hub.core.retry import RetryConfig

    from .models import (
        AllProvidersResponse,
        IPBanListResponse,
        IPBanStatusResponse,
        IPUnbanResponse,
        ProviderCreateResponse,
        ProviderResponse,
        ProviderTokenRefreshResponse,
        TokenRefreshResponse,
        UserCreateResponse,
        UserResponse,
        WhitelistAddResponse,
        WhitelistListResponse,
        WhitelistRemoveResponse,
    )

__all__ = ["AdminClient"]

T = TypeVar("T")

# ═══════════════════════════════════════════════════════════════════════════
# Sync VPN Client
# ═══════════════════════════════════════════════════════════════════════════


class AdminClient:
    """
    Sync Admin API client.

    Production-grade admin client with:
    - HMAC-SHA256 signature authentication
    - Automatic retries with exponential backoff
    - Pydantic models with validation
    - Comprehensive error handling
    - Request/response logging

    Example:
        with AdminClient(
            base_url="https://api.example.com",
            secret_key="admin-secret-key"
        ) as client:
            # Create user
            user = client.create_user(user_id=12345)
            print(f"Created user: {user.api_token}")

            # Ban IP
            ban = client.ban_ip("192.168.1.100", duration_seconds=3600)
            print(f"Banned until: {ban.banned_until}")

            # Add to whitelist
            client.add_to_whitelist("10.0.0.0/24", "Office network")
    """

    def __init__(
        self,
        base_url: str,
        secret_key: str,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """
        Initialize admin API client.

        Args:
            base_url: API base URL (e.g., "https://api.example.com")
            secret_key: Admin secret key for HMAC authentication
            timeout: Request timeout in seconds
            retry_config: Custom retry configuration
        """
        self._async_client = AsyncAdminClient(
            base_url=base_url,
            secret_key=secret_key,
            timeout=timeout,
            retry_config=retry_config,
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._owned_loop = False

    def __enter__(self) -> AdminClient:
        """Context manager entry."""
        self._loop = asyncio.new_event_loop()
        self._owned_loop = True
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._async_client.connect())
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self._loop and self._owned_loop:
            self._loop.run_until_complete(self._async_client.close())
            self._loop.close()
            self._loop = None
            self._owned_loop = False

    def _run(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Run async coroutine synchronously.

        Args:
            coro: Coroutine to run

        Returns:
            Coroutine result
        """
        if self._loop is not None and self._owned_loop:
            return self._loop.run_until_complete(coro)
        # If not in context manager, create temporary loop
        return asyncio.run(coro)

    # ═══════════════════════════════════════════════════════════════════════
    # User Management
    # ═══════════════════════════════════════════════════════════════════════

    def create_user(self, user_id: int) -> UserCreateResponse:
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
            user = client.create_user(user_id=12345)
            print(f"API Token: {user.api_token}")
            print(f"User Hash: {user.user_hash}")
        """
        return self._run(self._async_client.create_user(user_id))

    def get_user(self, user_id: int) -> UserResponse:
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
        return self._run(self._async_client.get_user(user_id))

    def delete_user(self, user_id: int) -> None:
        """
        Delete user account.

        Args:
            user_id: External user ID

        Raises:
            NotFoundError: User not found
            AuthenticationError: Invalid admin secret key
        """
        return self._run(self._async_client.delete_user(user_id))

    def set_user_status(
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

        return self._run(self._async_client.set_user_status(user_id, is_active))

    def refresh_token(self, user_id: int) -> TokenRefreshResponse:
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
            result = client.refresh_token(user_id=12345)
            print(f"New token: {result.new_api_token}")
        """

        return self._run(self._async_client.refresh_token(user_id))

    # ═══════════════════════════════════════════════════════════════════════
    # Provider Management
    # ═══════════════════════════════════════════════════════════════════════

    def get_providers(self) -> AllProvidersResponse:
        """
        Get all providers.

        Returns:
            Provider names mapped to provider hashes.

        Raises:
            AuthenticationError: Invalid admin secret key.

        Example:
            providers = client.get_providers()
            for name, provider_hash in providers.provider_hashes.items():
                print(f"{name}: {provider_hash}")
        """
        return self._run(self._async_client.get_providers())

    def create_provider(
        self,
        owner_hash: str,
        provider_name: str,
        provider_url: str | None = None,
    ) -> ProviderCreateResponse:
        """
        Create a new provider account.

        Args:
            owner_hash: Provider owner's hash.
            provider_name: Provider name.
            provider_url: Optional provider URL.

        Returns:
            Created provider data with generated API token.

        Raises:
            ValidationError: Invalid provider data.
            ConflictError: Provider already exists.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = client.create_provider(
                owner_hash="a1b2c3d4e5f6...",
                provider_name="vpn123",
                provider_url="https://example.com",
            )
            print(f"Provider hash: {provider.provider_hash}")
            print(f"API token: {provider.api_token}")
        """
        return self._run(
            self._async_client.create_provider(
                owner_hash=owner_hash,
                provider_name=provider_name,
                provider_url=provider_url,
            )
        )

    def get_provider(self, provider_hash: str) -> ProviderResponse:
        """
        Get provider information.

        Args:
            provider_hash: Provider hash.

        Returns:
            Provider data.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = client.get_provider("a1b2c3d4e5f6...")
            print(provider.provider_name)
            print(provider.api_token)
        """
        return self._run(self._async_client.get_provider(provider_hash))

    def delete_provider(self, provider_hash: str) -> None:
        """
        Delete a provider account.

        Args:
            provider_hash: Provider hash.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            client.delete_provider("a1b2c3d4e5f6...")
        """
        return self._run(self._async_client.delete_provider(provider_hash))

    def set_provider_status(
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
            provider = client.set_provider_status(
                provider_hash="a1b2c3d4e5f6...",
                is_active=False,
            )
            print(provider.is_active)
        """
        return self._run(
            self._async_client.set_provider_status(
                provider_hash=provider_hash,
                is_active=is_active,
            )
        )

    def update_provider_url(
        self,
        provider_hash: str,
        provider_url: str | None,
    ) -> ProviderResponse:
        """
        Update provider URL.

        Args:
            provider_hash: Provider hash.
            provider_url: New provider URL.

        Returns:
            Updated provider data.

        Raises:
            NotFoundError: Provider not found.
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = client.update_provider_url(
                provider_hash="a1b2c3d4e5f6...",
                provider_url="https://example.com",
            )
        """
        return self._run(
            self._async_client.update_provider_url(
                provider_hash=provider_hash,
                provider_url=provider_url,
            )
        )

    def update_provider_name(
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
            AuthenticationError: Invalid admin secret key.

        Example:
            provider = client.update_provider_name(
                provider_hash="a1b2c3d4e5f6...",
                provider_name="vpn123",
            )
        """
        return self._run(
            self._async_client.update_provider_name(
                provider_hash=provider_hash,
                provider_name=provider_name,
            )
        )

    def refresh_provider_token(
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
            result = client.refresh_provider_token(
                provider_hash="a1b2c3d4e5f6...",
            )
            print(f"New token: {result.new_api_token}")
        """
        return self._run(
            self._async_client.refresh_provider_token(
                provider_hash=provider_hash,
            )
        )

    # ═══════════════════════════════════════════════════════════════════════
    # IP Ban Management
    # ═══════════════════════════════════════════════════════════════════════

    def ban_ip(
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
            ban = client.ban_ip("192.168.1.100", duration_seconds=3600)
            print(f"Banned until: {ban.banned_until}")
            print(f"Remaining: {ban.remaining_seconds}s")

            # Ban with default duration
            ban = client.ban_ip("192.168.1.100")
        """

        return self._run(
            self._async_client.ban_ip(ip_address=ip_address, duration_seconds=duration_seconds)
        )

    def unban_ip(self, ip_address: str) -> IPUnbanResponse:
        """
        Unban IP address.

        Args:
            ip_address: IP address to unban

        Returns:
            Unban result

        Raises:
            AuthenticationError: Invalid admin secret key

        Example:
            result = client.unban_ip("192.168.1.100")
            if result.was_banned:
                print(f"Unbanned {result.ip_address}")
            else:
                print(f"{result.ip_address} was not banned")
        """

        return self._run(self._async_client.unban_ip(ip_address))

    def get_ban_status(self, ip_address: str) -> IPBanStatusResponse:
        """
        Check IP ban status.

        Args:
            ip_address: IP address to check

        Returns:
            Ban status

        Raises:
            AuthenticationError: Invalid admin secret key

        Example:
            status = client.get_ban_status("192.168.1.100")
            if status.is_banned:
                print(f"Banned until: {status.banned_until}")
                print(f"Remaining: {status.remaining_seconds}s")
            else:
                print("Not banned")
        """

        return self._run(self._async_client.get_ban_status(ip_address))

    def get_ban_list(self) -> IPBanListResponse:
        """
        Get all banned IPs.

        Returns:
            List of all bans

        Raises:
            AuthenticationError: Invalid admin secret key

        Example:
            bans = client.get_ban_list()
            print(f"Total bans: {bans.total}")
            for ban in bans.entries:
                print(f"  {ban.ip_address} until {ban.banned_until}")
        """

        return self._run(self._async_client.get_ban_list())

    # ═══════════════════════════════════════════════════════════════════════
    # Whitelist Management
    # ═══════════════════════════════════════════════════════════════════════

    def add_to_whitelist(
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
            result = client.add_to_whitelist(
                "10.0.0.0/24",
                description="Office network"
            )
            print(result.message)
        """

        return self._run(
            self._async_client.add_to_whitelist(ip_address=ip_address, description=description)
        )

    def remove_from_whitelist(self, ip_address: str) -> WhitelistRemoveResponse:
        """
        Remove IP from whitelist.

        Args:
            ip_address: IP address to remove

        Returns:
            Whitelist remove result

        Raises:
            AuthenticationError: Invalid admin secret key

        Example:
            result = client.remove_from_whitelist("10.0.0.0/24")
            if result.was_whitelisted:
                print(f"Removed {result.ip_address} from whitelist")
            else:
                print(f"{result.ip_address} was not whitelisted")
        """

        return self._run(self._async_client.remove_from_whitelist(ip_address=ip_address))

    def list_whitelist(self) -> WhitelistListResponse:
        """
        Get all whitelisted IPs.

        Returns:
            List of all whitelist entries

        Raises:
            AuthenticationError: Invalid admin secret key

        Example:
            whitelist = client.list_whitelist()
            print(f"Total entries: {whitelist.total}")
            for entry in whitelist.entries:
                print(f"  {entry.ip_address}: {entry.description}")
                print(f"    Added: {entry.added_at}")
        """

        return self._run(self._async_client.list_whitelist())

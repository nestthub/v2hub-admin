"""
Tests for the synchronous AdminClient provider authorization wrapper.

These don't re-test HTTP behavior (covered in
test_async_client_provider_authorization.py) - they confirm each sync
method correctly delegates to the underlying AsyncAdminClient with the
right arguments via respx-mocked responses.
"""

from __future__ import annotations

import httpx
import respx

from ._helpers import BASE_URL
from .test_client import make_sync_client


class TestSyncProviderAuthorizationDelegation:
    @respx.mock
    def test_get_provider_authorization(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/auth/vpn123/42").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_id": 42,
                    "provider_name": "vpn123",
                    "provider_url": None,
                    "status": "pending",
                },
            )
        )
        with make_sync_client() as client:
            result = client.get_provider_authorization("vpn123", 42)

        assert result.user_id == 42
        assert result.status == "pending"

    @respx.mock
    def test_process_provider_authorization(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_id": 42,
                    "provider_name": "vpn123",
                    "provider_url": None,
                    "status": "pending",
                },
            )
        )
        with make_sync_client() as client:
            result = client.process_provider_authorization(
                user_id=42,
                provider_name="vpn123",
                hmac="a1b2c3",
            )

        assert result.status == "pending"

    @respx.mock
    def test_process_provider_authorization_without_hmac(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_id": 42,
                    "provider_name": "vpn123",
                    "provider_url": None,
                    "status": "approved",
                },
            )
        )
        with make_sync_client() as client:
            result = client.process_provider_authorization(user_id=42, provider_name="vpn123")

        assert result.status == "approved"

    @respx.mock
    def test_approve_provider_authorization(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/approve").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_id": 42,
                    "provider_name": "vpn123",
                    "provider_url": "https://t.me/examplebot",
                    "status": "approved",
                },
            )
        )
        with make_sync_client() as client:
            result = client.approve_provider_authorization(user_id=42, provider_name="vpn123")

        assert result.status == "approved"

    @respx.mock
    def test_reject_provider_authorization(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/reject").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_id": 42,
                    "provider_name": "vpn123",
                    "provider_url": None,
                    "status": None,
                },
            )
        )
        with make_sync_client() as client:
            result = client.reject_provider_authorization(user_id=42, provider_name="vpn123")

        assert result.status is None

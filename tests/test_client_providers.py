"""
Tests for the synchronous AdminClient provider management wrapper.

These don't re-test HTTP behavior (covered in test_async_client_providers.py) -
they confirm each sync method correctly delegates to the underlying
AsyncAdminClient with the right arguments via respx-mocked responses.
"""

from __future__ import annotations

import httpx
import respx

from ._helpers import BASE_URL
from .test_client import make_sync_client


class TestSyncProviderDelegation:
    @respx.mock
    def test_get_providers(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers").mock(
            return_value=httpx.Response(200, json={"provider_hashes": {"vpn123": "p-hash"}})
        )
        with make_sync_client() as client:
            result = client.get_providers()
        assert result.provider_hashes == {"vpn123": "p-hash"}

    @respx.mock
    def test_create_provider(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": None,
                    "is_active": True,
                },
            )
        )
        with make_sync_client() as client:
            result = client.create_provider(owner_hash="o-hash", provider_name="vpn123")
        assert result.provider_hash == "p-hash"

    @respx.mock
    def test_get_provider(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/p-hash").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": None,
                    "is_active": True,
                },
            )
        )
        with make_sync_client() as client:
            result = client.get_provider("p-hash")
        assert result.provider_name == "vpn123"

    @respx.mock
    def test_delete_provider(self) -> None:
        route = respx.delete(f"{BASE_URL}/api/v1/admin/providers/p-hash").mock(
            return_value=httpx.Response(204)
        )
        with make_sync_client() as client:
            client.delete_provider("p-hash")
        assert route.called
        assert route.call_count == 1

    @respx.mock
    def test_set_provider_status(self) -> None:
        respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": None,
                    "is_active": False,
                },
            )
        )
        with make_sync_client() as client:
            result = client.set_provider_status("p-hash", is_active=False)
        assert result.is_active is False

    @respx.mock
    def test_update_provider_url(self) -> None:
        respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/url").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": "https://example.com",
                    "is_active": True,
                },
            )
        )
        with make_sync_client() as client:
            result = client.update_provider_url("p-hash", "https://example.com")
        assert result.provider_url == "https://example.com"

    @respx.mock
    def test_update_provider_name(self) -> None:
        respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/name").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "new-name",
                    "api_token": "p-hash:token",
                    "provider_url": None,
                    "is_active": True,
                },
            )
        )
        with make_sync_client() as client:
            result = client.update_provider_name("p-hash", "new-name")
        assert result.provider_name == "new-name"

    @respx.mock
    def test_refresh_provider_token(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/refresh-token").mock(
            return_value=httpx.Response(
                200,
                json={"provider_hash": "p-hash", "new_api_token": "p-hash:newtoken"},
            )
        )
        with make_sync_client() as client:
            result = client.refresh_provider_token("p-hash")
        assert result.new_api_token == "p-hash:newtoken"

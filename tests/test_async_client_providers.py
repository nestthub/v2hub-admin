"""
Tests for AsyncAdminClient provider management endpoints.

HTTP calls are intercepted with respx (mocking httpx's transport layer),
so no real network traffic occurs.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from v2hub.core.exceptions import NotFoundError

from ._helpers import BASE_URL, make_client


class TestProviderManagement:
    @respx.mock
    async def test_get_providers(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hashes": {
                        "Provider A": "hash-a",
                        "Provider B": "hash-b",
                    }
                },
            )
        )
        async with make_client() as client:
            result = await client.get_providers()

        assert result.provider_hashes == {"Provider A": "hash-a", "Provider B": "hash-b"}

    @respx.mock
    async def test_get_providers_empty(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers").mock(
            return_value=httpx.Response(200, json={"provider_hashes": {}})
        )
        async with make_client() as client:
            result = await client.get_providers()

        assert result.provider_hashes == {}

    @respx.mock
    async def test_create_provider(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": "https://t.me/examplebot",
                    "is_active": True,
                },
            )
        )
        async with make_client() as client:
            result = await client.create_provider(
                owner_hash="o-hash",
                provider_name="vpn123",
                provider_url="https://t.me/examplebot",
            )

        assert result.provider_hash == "p-hash"
        assert result.api_token == "p-hash:token"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {
            "owner_hash": "o-hash",
            "provider_name": "vpn123",
            "provider_url": "https://t.me/examplebot",
        }

    @respx.mock
    async def test_create_provider_without_url_omits_field_from_payload(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers").mock(
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
        async with make_client() as client:
            await client.create_provider(owner_hash="o-hash", provider_name="vpn123")

        sent_body = json.loads(route.calls[0].request.content)
        assert "provider_url" not in sent_body

    @respx.mock
    async def test_get_provider(self) -> None:
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
        async with make_client() as client:
            result = await client.get_provider("p-hash")

        assert result.provider_name == "vpn123"

    @respx.mock
    async def test_get_provider_by_name(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/name/vpn123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": "https://t.me/examplebot",
                    "is_active": True,
                },
            )
        )
        async with make_client() as client:
            result = await client.get_provider_by_name("vpn123")

        assert result.provider_hash == "p-hash"
        assert result.owner_hash == "o-hash"
        assert result.provider_name == "vpn123"
        assert result.api_token == "p-hash:token"
        assert result.provider_url == "https://t.me/examplebot"
        assert result.is_active is True

    @respx.mock
    async def test_get_provider_by_name_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/name/missing").mock(
            return_value=httpx.Response(404, json={"message": "Provider not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_provider_by_name("missing")

    @respx.mock
    async def test_get_provider_by_owner(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/owner/12345").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": "https://t.me/examplebot",
                    "is_active": True,
                },
            )
        )
        async with make_client() as client:
            result = await client.get_provider_by_owner_id(12345)

        assert result.provider_hash == "p-hash"
        assert result.owner_hash == "o-hash"
        assert result.provider_name == "vpn123"
        assert result.api_token == "p-hash:token"
        assert result.provider_url == "https://t.me/examplebot"
        assert result.is_active is True

    @respx.mock
    async def test_get_provider_by_owner_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/owner/99999").mock(
            return_value=httpx.Response(404, json={"message": "User not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_provider_by_owner_id(99999)

    @respx.mock
    async def test_get_user_providers(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/12345/providers").mock(
            return_value=httpx.Response(
                200,
                json={
                    "connections": [
                        {
                            "provider_name": "vpn123",
                            "provider_url": "https://t.me/examplebot",
                            "is_authorized": True,
                            "status": "approved",
                        },
                        {
                            "provider_name": "vpn456",
                            "provider_url": None,
                            "is_authorized": False,
                            "status": "pending",
                        },
                    ]
                },
            )
        )
        async with make_client() as client:
            result = await client.get_user_providers(12345)

        assert len(result.connections) == 2

        first = result.connections[0]
        assert first.provider_name == "vpn123"
        assert first.provider_url == "https://t.me/examplebot"
        assert first.is_authorized is True
        assert first.status == "approved"

        second = result.connections[1]
        assert second.provider_name == "vpn456"
        assert second.provider_url is None
        assert second.is_authorized is False
        assert second.status == "pending"

    @respx.mock
    async def test_get_user_providers_empty(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/12345/providers").mock(
            return_value=httpx.Response(
                200,
                json={"connections": []},
            )
        )
        async with make_client() as client:
            result = await client.get_user_providers(12345)

        assert result.connections == []

    @respx.mock
    async def test_get_user_providers_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/99999/providers").mock(
            return_value=httpx.Response(404, json={"message": "User not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_user_providers(99999)

    @respx.mock
    async def test_get_user_provider(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/12345/providers/vpn123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_name": "vpn123",
                    "provider_url": "https://t.me/examplebot",
                    "is_authorized": True,
                    "status": "approved",
                },
            )
        )
        async with make_client() as client:
            result = await client.get_user_provider(12345, "vpn123")

        assert result.provider_name == "vpn123"
        assert result.provider_url == "https://t.me/examplebot"
        assert result.is_authorized is True
        assert result.status == "approved"

    @respx.mock
    async def test_get_user_provider_not_connected(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/12345/providers/vpn123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_name": "vpn123",
                    "provider_url": "https://t.me/examplebot",
                    "is_authorized": False,
                    "status": None,
                },
            )
        )
        async with make_client() as client:
            result = await client.get_user_provider(12345, "vpn123")

        assert result.provider_name == "vpn123"
        assert result.provider_url == "https://t.me/examplebot"
        assert result.is_authorized is False
        assert result.status is None

    @respx.mock
    async def test_get_user_provider_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/12345/providers/missing").mock(
            return_value=httpx.Response(404, json={"message": "Provider not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_user_provider(12345, "missing")

    @respx.mock
    async def test_get_provider_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/missing").mock(
            return_value=httpx.Response(404, json={"message": "Provider not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_provider("missing")

    @respx.mock
    async def test_delete_provider(self) -> None:
        route = respx.delete(f"{BASE_URL}/api/v1/admin/providers/p-hash").mock(
            return_value=httpx.Response(204)
        )
        async with make_client() as client:
            await client.delete_provider("p-hash")

        assert route.called
        assert route.call_count == 1

    @respx.mock
    async def test_delete_provider_not_found_raises(self) -> None:
        respx.delete(f"{BASE_URL}/api/v1/admin/providers/missing").mock(
            return_value=httpx.Response(404, json={"message": "Provider not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.delete_provider("missing")

    @respx.mock
    async def test_set_provider_status(self) -> None:
        route = respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/status").mock(
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
        async with make_client() as client:
            result = await client.set_provider_status("p-hash", is_active=False)

        assert result.is_active is False
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"is_active": False}

    @respx.mock
    async def test_update_provider_url(self) -> None:
        route = respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/url").mock(
            return_value=httpx.Response(
                200,
                json={
                    "provider_hash": "p-hash",
                    "owner_hash": "o-hash",
                    "provider_name": "vpn123",
                    "api_token": "p-hash:token",
                    "provider_url": "https://t.me/newbot",
                    "is_active": True,
                },
            )
        )
        async with make_client() as client:
            result = await client.update_provider_url("p-hash", "https://t.me/newbot")

        assert result.provider_url == "https://t.me/newbot"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"provider_url": "https://t.me/newbot"}

    @respx.mock
    async def test_update_provider_url_to_none(self) -> None:
        route = respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/url").mock(
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
        async with make_client() as client:
            result = await client.update_provider_url("p-hash", None)

        assert result.provider_url is None
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"provider_url": None}

    @respx.mock
    async def test_update_provider_name(self) -> None:
        route = respx.patch(f"{BASE_URL}/api/v1/admin/providers/p-hash/name").mock(
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
        async with make_client() as client:
            result = await client.update_provider_name("p-hash", "new-name")

        assert result.provider_name == "new-name"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"provider_name": "new-name"}

    @respx.mock
    async def test_refresh_provider_token(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers/refresh-token").mock(
            return_value=httpx.Response(
                200,
                json={"provider_hash": "p-hash", "new_api_token": "p-hash:newtoken"},
            )
        )
        async with make_client() as client:
            result = await client.refresh_provider_token("p-hash")

        assert result.new_api_token == "p-hash:newtoken"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"provider_hash": "p-hash"}

    @respx.mock
    async def test_refresh_provider_token_not_found_raises(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/refresh-token").mock(
            return_value=httpx.Response(404, json={"message": "Provider not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.refresh_provider_token("missing")

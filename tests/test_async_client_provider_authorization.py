"""
Tests for AsyncAdminClient provider authorization endpoints.

HTTP calls are intercepted with respx (mocking httpx's transport layer),
so no real network traffic occurs.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from v2hub.core.exceptions import AuthenticationError, ConflictError, NotFoundError

from ._helpers import BASE_URL, make_client


class TestGetProviderAuthorization:
    @respx.mock
    async def test_returns_authorization_info(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/auth/vpn123/42").mock(
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
        async with make_client() as client:
            result = await client.get_provider_authorization("vpn123", 42)

        assert result.user_id == 42
        assert result.provider_name == "vpn123"
        assert result.provider_url == "https://t.me/examplebot"
        assert result.status == "approved"

    @respx.mock
    async def test_status_none_when_no_authorization_exists(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/auth/vpn123/42").mock(
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
        async with make_client() as client:
            result = await client.get_provider_authorization("vpn123", 42)

        assert result.status is None

    @respx.mock
    async def test_uses_get_and_positional_url_order(self) -> None:
        """provider_name and user_id must appear in the URL in that order."""
        route = respx.get(f"{BASE_URL}/api/v1/admin/providers/auth/vpn123/42").mock(
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
        async with make_client() as client:
            await client.get_provider_authorization(provider_name="vpn123", user_id=42)

        assert route.called
        assert route.calls[0].request.method == "GET"

    @respx.mock
    async def test_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/auth/missing/42").mock(
            return_value=httpx.Response(404, json={"message": "Authorization not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_provider_authorization("missing", 42)

    @respx.mock
    async def test_authentication_error_propagates(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/providers/auth/vpn123/42").mock(
            return_value=httpx.Response(401, json={"message": "Invalid signature"})
        )
        async with make_client() as client:
            with pytest.raises(AuthenticationError):
                await client.get_provider_authorization("vpn123", 42)


class TestProcessProviderAuthorization:
    @respx.mock
    async def test_sends_user_id_provider_name_and_hmac(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers/auth").mock(
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
        async with make_client() as client:
            result = await client.process_provider_authorization(
                user_id=42,
                provider_name="vpn123",
                hmac="a1b2c3",
            )

        assert result.status == "pending"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {
            "user_id": 42,
            "provider_name": "vpn123",
            "hmac": "a1b2c3",
        }

    @respx.mock
    async def test_omits_hmac_from_payload_when_not_provided(self) -> None:
        """hmac is optional; querying an existing authorization needs none."""
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers/auth").mock(
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
        async with make_client() as client:
            await client.process_provider_authorization(user_id=42, provider_name="vpn123")

        sent_body = json.loads(route.calls[0].request.content)
        assert "hmac" not in sent_body

    @respx.mock
    async def test_invalid_hmac_raises_authentication_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth").mock(
            return_value=httpx.Response(401, json={"message": "Invalid HMAC"})
        )
        async with make_client() as client:
            with pytest.raises(AuthenticationError):
                await client.process_provider_authorization(
                    user_id=42,
                    provider_name="vpn123",
                    hmac="bad-hmac",
                )

    @respx.mock
    async def test_provider_not_found_raises(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth").mock(
            return_value=httpx.Response(404, json={"message": "Provider not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.process_provider_authorization(
                    user_id=42,
                    provider_name="missing",
                    hmac="a1b2c3",
                )


class TestApproveProviderAuthorization:
    @respx.mock
    async def test_approves_pending_authorization(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/approve").mock(
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
        async with make_client() as client:
            result = await client.approve_provider_authorization(
                user_id=42,
                provider_name="vpn123",
            )

        assert result.status == "approved"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"user_id": 42, "provider_name": "vpn123"}

    @respx.mock
    async def test_non_pending_authorization_raises_conflict(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/approve").mock(
            return_value=httpx.Response(
                409, json={"error_type": "conflict", "message": "Authorization is not pending"}
            )
        )
        async with make_client() as client:
            with pytest.raises(ConflictError):
                await client.approve_provider_authorization(user_id=42, provider_name="vpn123")

    @respx.mock
    async def test_provider_limit_reached_raises_conflict(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/approve").mock(
            return_value=httpx.Response(
                409,
                json={"error_type": "conflict", "message": "Provider limit reached"},
            )
        )
        async with make_client() as client:
            with pytest.raises(ConflictError):
                await client.approve_provider_authorization(user_id=42, provider_name="vpn123")

    @respx.mock
    async def test_not_found_raises(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/approve").mock(
            return_value=httpx.Response(404, json={"message": "Authorization not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.approve_provider_authorization(user_id=42, provider_name="missing")


class TestRejectProviderAuthorization:
    @respx.mock
    async def test_rejects_pending_authorization(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/reject").mock(
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
        async with make_client() as client:
            result = await client.reject_provider_authorization(
                user_id=42,
                provider_name="vpn123",
            )

        assert result.status is None
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"user_id": 42, "provider_name": "vpn123"}

    @respx.mock
    async def test_revoked_when_authorization_had_subscriptions(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/reject").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_id": 42,
                    "provider_name": "vpn123",
                    "provider_url": None,
                    "status": "revoked",
                },
            )
        )
        async with make_client() as client:
            result = await client.reject_provider_authorization(
                user_id=42,
                provider_name="vpn123",
            )

        assert result.status == "revoked"

    @respx.mock
    async def test_non_pending_authorization_raises_conflict(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/reject").mock(
            return_value=httpx.Response(
                409, json={"error_type": "conflict", "message": "Authorization is not pending"}
            )
        )
        async with make_client() as client:
            with pytest.raises(ConflictError):
                await client.reject_provider_authorization(user_id=42, provider_name="vpn123")

    @respx.mock
    async def test_not_found_raises(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/providers/auth/reject").mock(
            return_value=httpx.Response(404, json={"message": "Authorization not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.reject_provider_authorization(user_id=42, provider_name="missing")

"""
Tests for AsyncAdminClient.

HTTP calls are intercepted with respx (mocking httpx's transport layer),
so no real network traffic occurs. This also lets us assert on the
signature headers that AdminAuthenticator attaches to each request.
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx
import pytest
import respx

from v2hub.core.exceptions import AuthenticationError, NotFoundError, VPNAPIError

from ._helpers import BASE_URL, NO_DELAY_RETRY, make_client


class TestClientLifecycle:
    async def test_context_manager_connects_and_closes(self) -> None:
        async with make_client() as client:
            assert client._http_client._client is not None
        assert client._http_client._client is None

    async def test_connect_and_close_explicit(self) -> None:
        client = make_client()
        await client.connect()
        assert client._http_client._client is not None
        await client.close()
        assert client._http_client._client is None


class TestRequestSigning:
    @respx.mock
    async def test_get_request_includes_signature_headers(self) -> None:
        route = respx.get(f"{BASE_URL}/api/v1/admin/users/1").mock(
            return_value=httpx.Response(
                200, json={"user_hash": "h", "user_id": 1, "api_token": "1:h", "is_active": True}
            )
        )
        async with make_client() as client:
            await client.get_user(1)

        sent_request = route.calls[0].request
        assert "x-signature" in sent_request.headers
        assert "x-timestamp" in sent_request.headers
        assert len(sent_request.headers["x-signature"]) == 64

    @respx.mock
    async def test_post_request_body_included_in_signature_payload(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/users").mock(
            return_value=httpx.Response(
                200, json={"user_hash": "h", "user_id": 5, "api_token": "5:h", "is_active": True}
            )
        )
        async with make_client() as client:
            await client.create_user(user_id=5)

        sent_request = route.calls[0].request
        assert json.loads(sent_request.content) == {"user_id": 5}


class TestUserManagement:
    @respx.mock
    async def test_create_user(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/users").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_hash": "abc123",
                    "user_id": 12345,
                    "api_token": "12345:abc123",
                    "is_active": True,
                },
            )
        )
        async with make_client() as client:
            result = await client.create_user(user_id=12345)

        assert result.user_id == 12345
        assert result.api_token == "12345:abc123"

    @respx.mock
    async def test_get_user(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/42").mock(
            return_value=httpx.Response(
                200,
                json={
                    "user_hash": "h",
                    "user_id": 42,
                    "api_token": "42:h",
                    "is_active": True,
                },
            )
        )
        async with make_client() as client:
            result = await client.get_user(42)

        assert result.user_id == 42

    @respx.mock
    async def test_get_user_not_found_raises(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/999").mock(
            return_value=httpx.Response(404, json={"message": "User not found"})
        )
        async with make_client() as client:
            with pytest.raises(NotFoundError):
                await client.get_user(999)

    @respx.mock
    async def test_delete_user(self) -> None:
        route = respx.delete(f"{BASE_URL}/api/v1/admin/users/7").mock(
            return_value=httpx.Response(204)
        )
        async with make_client() as client:
            await client.delete_user(7)

        assert route.called
        assert route.call_count == 1

    @respx.mock
    async def test_set_user_status(self) -> None:
        respx.patch(f"{BASE_URL}/api/v1/admin/users/1/status").mock(
            return_value=httpx.Response(
                200,
                json={"user_hash": "h", "user_id": 1, "api_token": "1:h", "is_active": False},
            )
        )
        async with make_client() as client:
            result = await client.set_user_status(1, is_active=False)

        assert result.is_active is False

    @respx.mock
    async def test_refresh_token(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/users/refresh-token").mock(
            return_value=httpx.Response(200, json={"user_id": 1, "new_api_token": "1:newtoken"})
        )
        async with make_client() as client:
            result = await client.refresh_token(1)

        assert result.new_api_token == "1:newtoken"

    @respx.mock
    async def test_authentication_error_propagates(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/1").mock(
            return_value=httpx.Response(401, json={"message": "Invalid signature"})
        )
        async with make_client() as client:
            with pytest.raises(AuthenticationError):
                await client.get_user(1)


class TestIPBanManagement:
    @respx.mock
    async def test_ban_ip_with_duration(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(
                200,
                json={
                    "ip_address": "192.168.1.100",
                    "is_banned": True,
                    "banned_until": "2026-04-20T12:00:00",
                    "remaining_seconds": 3600,
                },
            )
        )
        async with make_client() as client:
            result = await client.ban_ip("192.168.1.100", duration_seconds=3600)

        assert result.is_banned is True
        assert result.remaining_seconds == 3600
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"ip_address": "192.168.1.100", "duration_seconds": 3600}

    @respx.mock
    async def test_ban_ip_without_duration_omits_field_from_payload(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(
                200, json={"ip_address": "192.168.1.100", "is_banned": True}
            )
        )
        async with make_client() as client:
            await client.ban_ip("192.168.1.100")

        sent_body = json.loads(route.calls[0].request.content)
        assert "duration_seconds" not in sent_body

    @respx.mock
    async def test_unban_ip(self) -> None:
        respx.delete(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(
                200,
                json={
                    "ip_address": "192.168.1.100",
                    "was_banned": True,
                    "message": "unbanned",
                },
            )
        )
        async with make_client() as client:
            result = await client.unban_ip("192.168.1.100")

        assert result.was_banned is True

    @respx.mock
    async def test_get_ban_status(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/bans/192.168.1.100").mock(
            return_value=httpx.Response(
                200, json={"ip_address": "192.168.1.100", "is_banned": False}
            )
        )
        async with make_client() as client:
            result = await client.get_ban_status("192.168.1.100")

        assert result.is_banned is False

    @respx.mock
    async def test_get_ban_list(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entries": [{"ip_address": "192.168.1.100", "banned_until": None}],
                    "total": 1,
                },
            )
        )
        async with make_client() as client:
            result = await client.get_ban_list()

        assert result.total == 1
        assert result.entries[0].ip_address == "192.168.1.100"

    @respx.mock
    async def test_get_ban_list_empty(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(200, json={"entries": [], "total": 0})
        )
        async with make_client() as client:
            result = await client.get_ban_list()

        assert result.entries == []
        assert result.total == 0


class TestWhitelistManagement:
    @respx.mock
    async def test_add_to_whitelist(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(
                200,
                json={
                    "ip_address": "10.0.0.0/24",
                    "description": "Office network",
                    "message": "added",
                },
            )
        )
        async with make_client() as client:
            result = await client.add_to_whitelist("10.0.0.0/24", description="Office network")

        assert result.message == "added"
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"ip_address": "10.0.0.0/24", "description": "Office network"}

    @respx.mock
    async def test_add_to_whitelist_without_description_omits_field(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(200, json={"ip_address": "10.0.0.0/24", "message": "added"})
        )
        async with make_client() as client:
            await client.add_to_whitelist("10.0.0.0/24")

        sent_body = json.loads(route.calls[0].request.content)
        assert "description" not in sent_body

    @respx.mock
    async def test_remove_from_whitelist(self) -> None:
        respx.delete(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(
                200,
                json={
                    "ip_address": "10.0.0.0/24",
                    "was_whitelisted": True,
                    "message": "removed",
                },
            )
        )
        async with make_client() as client:
            result = await client.remove_from_whitelist("10.0.0.0/24")

        assert result.was_whitelisted is True

    @respx.mock
    async def test_list_whitelist(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entries": [
                        {
                            "ip_address": "10.0.0.0/24",
                            "description": "Office",
                            "added_at": "2026-04-20T10:00:00",
                        }
                    ],
                    "total": 1,
                },
            )
        )
        async with make_client() as client:
            result = await client.list_whitelist()

        assert result.total == 1
        assert result.entries[0].description == "Office"

    @respx.mock
    async def test_list_whitelist_empty(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(200, json={"entries": [], "total": 0})
        )
        async with make_client() as client:
            result = await client.list_whitelist()

        assert result.entries == []


class TestUsageStatistics:
    @respx.mock
    async def test_get_stats_without_arguments(self) -> None:
        """No filters -> the query string is empty (params are all None)."""
        route = respx.get(f"{BASE_URL}/api/v1/admin/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "general": {
                        "total_users": 1542,
                        "new_users": 45,
                        "new_subscriptions": 12,
                    }
                },
            )
        )
        async with make_client() as client:
            result = await client.get_stats()

        assert result.general.total_users == 1542
        sent_url = route.calls[0].request.url
        assert sent_url.query == b""

    @respx.mock
    async def test_get_stats_with_period(self) -> None:
        route = respx.get(f"{BASE_URL}/api/v1/admin/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "general": {
                        "total_users": 10,
                        "new_users": 1,
                        "new_subscriptions": 2,
                    }
                },
            )
        )
        async with make_client() as client:
            result = await client.get_stats(period="week")

        assert result.general.new_users == 1
        sent_params = dict(route.calls[0].request.url.params)
        assert sent_params == {"period": "week"}

    @respx.mock
    async def test_get_stats_with_explicit_date_range(self) -> None:
        route = respx.get(f"{BASE_URL}/api/v1/admin/stats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "general": {
                        "total_users": 10,
                        "new_users": 1,
                        "new_subscriptions": 2,
                    }
                },
            )
        )
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)
        async with make_client() as client:
            await client.get_stats(start_date=start, end_date=end)

        sent_params = dict(route.calls[0].request.url.params)
        assert sent_params["start_date"] == start.isoformat()
        assert sent_params["end_date"] == end.isoformat()
        assert "period" not in sent_params

    @respx.mock
    async def test_authentication_error_propagates(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/stats").mock(
            return_value=httpx.Response(401, json={"message": "Invalid signature"})
        )
        async with make_client() as client:
            with pytest.raises(AuthenticationError):
                await client.get_stats()


class TestGenericErrorHandling:
    @respx.mock
    async def test_server_error_raises_vpnapi_error_subclass(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        async with make_client(retry_config=NO_DELAY_RETRY) as client:
            with pytest.raises(VPNAPIError):
                await client.list_whitelist()

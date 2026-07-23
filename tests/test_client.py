"""
Tests for the synchronous AdminClient wrapper.

These don't re-test HTTP behavior (covered in test_async_client.py) -
they confirm each sync method correctly delegates to the underlying
AsyncAdminClient with the right arguments via respx-mocked responses.
"""

from __future__ import annotations

import httpx
import respx

from v2hub_admin.client import AdminClient

from ._helpers import BASE_URL, SECRET_KEY


def make_sync_client(**kwargs: object) -> AdminClient:
    params: dict[str, object] = {"base_url": BASE_URL, "secret_key": SECRET_KEY}
    params.update(kwargs)
    return AdminClient(**params)  # type: ignore[arg-type]


class TestSyncClientLifecycle:
    def test_context_manager_sets_up_and_tears_down_loop(self) -> None:
        with make_sync_client() as client:
            assert client._loop is not None
        assert client._loop is None


class TestSyncClientDelegation:
    @respx.mock
    def test_create_user(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/users").mock(
            return_value=httpx.Response(
                200,
                json={"user_hash": "h", "user_id": 1, "api_token": "1:h", "is_active": True},
            )
        )
        with make_sync_client() as client:
            result = client.create_user(user_id=1)
        assert result.user_id == 1

    @respx.mock
    def test_get_user(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/users/1").mock(
            return_value=httpx.Response(
                200,
                json={"user_hash": "h", "user_id": 1, "api_token": "1:h", "is_active": True},
            )
        )
        with make_sync_client() as client:
            result = client.get_user(1)
        assert result.user_id == 1

    @respx.mock
    def test_delete_user(self) -> None:
        route = respx.delete(f"{BASE_URL}/api/v1/admin/users/1").mock(
            return_value=httpx.Response(204)
        )
        with make_sync_client() as client:
            client.delete_user(1)
        assert route.called
        assert route.call_count == 1

    @respx.mock
    def test_set_user_status(self) -> None:
        respx.patch(f"{BASE_URL}/api/v1/admin/users/1/status").mock(
            return_value=httpx.Response(
                200,
                json={"user_hash": "h", "user_id": 1, "api_token": "1:h", "is_active": False},
            )
        )
        with make_sync_client() as client:
            result = client.set_user_status(1, is_active=False)
        assert result.is_active is False

    @respx.mock
    def test_refresh_token(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/users/refresh-token").mock(
            return_value=httpx.Response(200, json={"user_id": 1, "new_api_token": "1:new"})
        )
        with make_sync_client() as client:
            result = client.refresh_token(1)
        assert result.new_api_token == "1:new"

    @respx.mock
    def test_ban_ip(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(200, json={"ip_address": "1.2.3.4", "is_banned": True})
        )
        with make_sync_client() as client:
            result = client.ban_ip("1.2.3.4", duration_seconds=60)
        assert result.is_banned is True

    @respx.mock
    def test_unban_ip(self) -> None:
        respx.delete(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(
                200,
                json={"ip_address": "192.168.1.100", "was_banned": True, "message": "unbanned"},
            )
        )
        with make_sync_client() as client:
            result = client.unban_ip("192.168.1.100")
        assert result.was_banned is True

    @respx.mock
    def test_get_ban_status(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/bans/1.2.3.4").mock(
            return_value=httpx.Response(200, json={"ip_address": "1.2.3.4", "is_banned": False})
        )
        with make_sync_client() as client:
            result = client.get_ban_status("1.2.3.4")
        assert result.is_banned is False

    @respx.mock
    def test_get_ban_list(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/bans").mock(
            return_value=httpx.Response(200, json={"entries": [], "total": 0})
        )
        with make_sync_client() as client:
            result = client.get_ban_list()
        assert result.total == 0

    @respx.mock
    def test_add_to_whitelist(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(200, json={"ip_address": "10.0.0.0/24", "message": "added"})
        )
        with make_sync_client() as client:
            result = client.add_to_whitelist("10.0.0.0/24", description="Office")
        assert result.message == "added"

    @respx.mock
    def test_remove_from_whitelist(self) -> None:
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
        with make_sync_client() as client:
            result = client.remove_from_whitelist("10.0.0.0/24")
        assert result.was_whitelisted is True

    @respx.mock
    def test_list_whitelist(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(200, json={"entries": [], "total": 0})
        )
        with make_sync_client() as client:
            result = client.list_whitelist()
        assert result.entries == []


class TestSyncClientWithoutContextManager:
    @respx.mock
    def test_run_without_entering_context_uses_asyncio_run(self) -> None:
        respx.get(f"{BASE_URL}/api/v1/admin/whitelist").mock(
            return_value=httpx.Response(200, json={"entries": [], "total": 0})
        )
        client = make_sync_client()
        # Never entered via `with`, so _run() should fall back to asyncio.run().
        result = client.list_whitelist()
        assert result.total == 0

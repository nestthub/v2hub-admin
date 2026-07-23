"""
Contract test for the public v2hub_admin package surface.

This does not test behavior, only that names importable from `v2hub_admin`
today remain importable after an update. If a name is intentionally removed
or renamed, this test should be updated deliberately so the change is
visible in the diff/changelog.
"""

from __future__ import annotations

from typing import ClassVar

import v2hub_admin

EXPECTED_EXPORTS = {
    "AdminClient",
    "AsyncAdminClient",
    "__version__",
}


class TestPublicAPISurface:
    def test_all_matches_expected_exports(self) -> None:
        assert set(v2hub_admin.__all__) == EXPECTED_EXPORTS

    def test_every_declared_export_is_actually_importable(self) -> None:
        missing = [name for name in v2hub_admin.__all__ if not hasattr(v2hub_admin, name)]
        assert missing == []

    def test_version_is_a_string(self) -> None:
        assert isinstance(v2hub_admin.__version__, str)
        assert v2hub_admin.__version__

    def test_api_version_is_v1(self) -> None:
        # Bumping this changes every endpoint URL the clients call.
        assert v2hub_admin.__api_version__ == "v1"

    def test_async_client_is_the_full_featured_client(self) -> None:
        from v2hub_admin.async_client import AsyncAdminClient

        assert v2hub_admin.AsyncAdminClient is AsyncAdminClient

    def test_sync_client_is_the_wrapper(self) -> None:
        from v2hub_admin.client import AdminClient

        assert v2hub_admin.AdminClient is AdminClient


class TestAsyncAdminClientMethodSurface:
    """
    Pin down the set of public methods on AsyncAdminClient. If an update
    silently removes/renames an existing method, that's a breaking change
    this test will catch.
    """

    EXPECTED_METHODS: ClassVar[set[str]] = {
        "create_user",
        "get_user",
        "delete_user",
        "set_user_status",
        "refresh_token",
        "ban_ip",
        "unban_ip",
        "get_ban_status",
        "get_ban_list",
        "add_to_whitelist",
        "remove_from_whitelist",
        "list_whitelist",
        "connect",
        "close",
    }

    def test_has_all_expected_methods(self) -> None:
        from v2hub_admin.async_client import AsyncAdminClient

        actual = {
            name
            for name in dir(AsyncAdminClient)
            if not name.startswith("_") and callable(getattr(AsyncAdminClient, name))
        }
        missing = self.EXPECTED_METHODS - actual
        assert missing == set(), f"Methods removed or renamed: {missing}"


class TestAdminClientMethodSurface:
    EXPECTED_METHODS: ClassVar[set[str]] = {
        "create_user",
        "get_user",
        "delete_user",
        "set_user_status",
        "refresh_token",
        "ban_ip",
        "unban_ip",
        "get_ban_status",
        "get_ban_list",
        "add_to_whitelist",
        "remove_from_whitelist",
        "list_whitelist",
    }

    def test_has_all_expected_methods(self) -> None:
        from v2hub_admin.client import AdminClient

        actual = {
            name
            for name in dir(AdminClient)
            if not name.startswith("_") and callable(getattr(AdminClient, name))
        }
        missing = self.EXPECTED_METHODS - actual
        assert missing == set(), f"Methods removed or renamed: {missing}"

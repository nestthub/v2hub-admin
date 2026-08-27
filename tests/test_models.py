"""
Tests for v2hub_admin Pydantic models.

Client-level tests (test_async_client*.py, test_client*.py) exercise these
models indirectly through HTTP round-trips. This file covers model
behavior in isolation: defaults, optional fields, and serialization.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from v2hub_admin.models import (
    ProviderAuthorizationBaseRequest,
    ProviderAuthorizationDecisionRequest,
    ProviderAuthorizationInfoResponse,
    ProviderAuthorizationRequest,
)


class TestProviderAuthorizationBaseRequest:
    def test_requires_user_id_and_provider_name(self) -> None:
        with pytest.raises(ValidationError):
            ProviderAuthorizationBaseRequest()  # type: ignore[call-arg]

    def test_accepts_valid_fields(self) -> None:
        req = ProviderAuthorizationBaseRequest(user_id=42, provider_name="vpn123")
        assert req.user_id == 42
        assert req.provider_name == "vpn123"


class TestProviderAuthorizationInfoResponse:
    def test_status_defaults_to_none(self) -> None:
        resp = ProviderAuthorizationInfoResponse(
            user_id=42,
            provider_name="vpn123",
            provider_url=None,
        )
        assert resp.status is None

    def test_accepts_known_status(self) -> None:
        resp = ProviderAuthorizationInfoResponse(
            user_id=42,
            provider_name="vpn123",
            provider_url="https://t.me/examplebot",
            status="approved",
        )
        assert resp.status == "approved"

    def test_unknown_status_falls_back_to_unknown(self) -> None:
        """ProviderAuthorizationStatus._missing_ maps unrecognized values."""
        resp = ProviderAuthorizationInfoResponse(
            user_id=42,
            provider_name="vpn123",
            provider_url=None,
            status="some-new-status-the-client-doesnt-know-about",
        )
        assert resp.status == "unknown"

    def test_provider_url_required_but_nullable(self) -> None:
        """provider_url has no default -- it must be passed, but None is valid."""
        with pytest.raises(ValidationError):
            ProviderAuthorizationInfoResponse(user_id=42, provider_name="vpn123")  # type: ignore[call-arg]


class TestProviderAuthorizationRequest:
    def test_hmac_defaults_to_none(self) -> None:
        req = ProviderAuthorizationRequest(user_id=42, provider_name="vpn123")
        assert req.hmac is None

    def test_hmac_excluded_from_payload_when_none(self) -> None:
        req = ProviderAuthorizationRequest(user_id=42, provider_name="vpn123")
        dumped = req.model_dump(mode="json", exclude_none=True)
        assert "hmac" not in dumped

    def test_hmac_included_when_provided(self) -> None:
        req = ProviderAuthorizationRequest(user_id=42, provider_name="vpn123", hmac="a1b2c3")
        dumped = req.model_dump(mode="json", exclude_none=True)
        assert dumped["hmac"] == "a1b2c3"


class TestProviderAuthorizationDecisionRequest:
    def test_carries_only_base_fields(self) -> None:
        req = ProviderAuthorizationDecisionRequest(user_id=42, provider_name="vpn123")
        assert req.model_dump(mode="json") == {"user_id": 42, "provider_name": "vpn123"}

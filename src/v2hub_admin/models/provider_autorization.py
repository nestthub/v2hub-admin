"""
Pydantic models for Admin API provider authorization endpoints.

Covers the authorization handshake between a provider and a user: a
provider requests access to manage a user's subscriptions, and an admin
(or the user, depending on deployment) approves or rejects that request.
"""

from pydantic import Field

from v2hub.models import ProviderAuthorizationStatus
from v2hub_admin.models.base import AdminBaseModel


class ProviderAuthorizationBaseRequest(AdminBaseModel):
    """Shared fields identifying a provider/user authorization pair."""

    user_id: int = Field(
        description="User ID",
    )
    provider_name: str = Field(
        description="Provider name",
    )


class ProviderAuthorizationInfoResponse(ProviderAuthorizationBaseRequest):
    """Current authorization state between a provider and a user."""

    provider_url: str | None = Field(
        description="Provider URL",
    )
    status: ProviderAuthorizationStatus | None = Field(
        default=None,
        description=(
            "Current authorization status. None when no authorization "
            "record exists (e.g. after it has been deleted)."
        ),
    )


class ProviderAuthorizationRequest(ProviderAuthorizationBaseRequest):
    """Request to create or query a provider authorization."""

    hmac: str | None = Field(
        default=None,
        description=(
            "Authorization HMAC issued with a connection invite. Required "
            "to create a new authorization; omit to query an existing one."
        ),
    )


class ProviderAuthorizationDecisionRequest(ProviderAuthorizationBaseRequest):
    """Request to approve or reject a pending provider authorization."""

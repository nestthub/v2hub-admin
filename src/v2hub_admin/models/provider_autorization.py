from pydantic import Field

from v2hub.models import ProviderAuthorizationStatus
from v2hub_admin.models.base import AdminBaseModel


class ProviderAuthorizationBaseRequest(AdminBaseModel):
    user_id: int = Field(
        description="User ID",
    )
    provider_name: str = Field(
        description="Provider name",
    )


class ProviderAuthorizationInfoResponse(ProviderAuthorizationBaseRequest):
    provider_url: str | None = Field(
        description="Provider URL",
    )
    status: ProviderAuthorizationStatus | None = Field(
        default=None,
        description="Current authorization status",
    )


class ProviderAuthorizationRequest(ProviderAuthorizationBaseRequest):
    hmac: str | None = Field(
        default=None,
        description="Authorization HMAC",
    )


class ProviderAuthorizationDecisionRequest(ProviderAuthorizationBaseRequest):
    pass

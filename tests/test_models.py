"""
Shared test helpers for v2hub_admin tests.
"""

from __future__ import annotations

from v2hub.core.retry import RetryConfig
from v2hub_admin.async_client import AsyncAdminClient

BASE_URL = "https://api.example.com"
SECRET_KEY = "test-secret-key"

# Retry config with zero delay so retry-path tests run instantly.
NO_DELAY_RETRY = RetryConfig(max_retries=2, initial_delay=0.0, max_delay=0.0, jitter=False)


def make_client(**kwargs: object) -> AsyncAdminClient:
    """Create an AsyncAdminClient pointed at a fixed base URL/secret for tests."""
    params: dict[str, object] = {
        "base_url": BASE_URL,
        "secret_key": SECRET_KEY,
    }
    params.update(kwargs)
    return AsyncAdminClient(**params)  # type: ignore[arg-type]

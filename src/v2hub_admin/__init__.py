"""
V2Hub API Client Library (Admin optional)
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, metadata, version

try:
    __version__ = version("v2hub-admin")
    __author__ = metadata("v2hub-admin")["Author-email"]
except PackageNotFoundError:
    __version__ = "unknown"
    __author__ = "unknown"

__api_version__ = "v1"

__all__ = [
    "AdminClient",
    "AsyncAdminClient",
    "__version__",
]

# ═════════════════════════════════════════════════════════════
# Admin client (explicit separation)
# ═════════════════════════════════════════════════════════════

from .async_client import AsyncAdminClient
from .client import AdminClient

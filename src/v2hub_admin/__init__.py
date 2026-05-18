"""
V2Hub API Client Library (Admin optional)
"""

from __future__ import annotations

__version__ = "1.0.2"
__author__ = "nestt"

__all__ = [
    # Version
    "__version__",

    # Admin client (explicit opt-in)
    "AsyncAdminClient",
    "AdminClient",

]

# ═════════════════════════════════════════════════════════════
# Admin client (explicit separation)
# ═════════════════════════════════════════════════════════════

from .async_client import AsyncAdminClient
from .client import AdminClient

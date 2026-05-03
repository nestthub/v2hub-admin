"""
HMAC authentication for admin API requests.

Implements signature-based authentication using HMAC-SHA256.
"""

from __future__ import annotations

import hashlib
import hmac
import time

__all__ = ["AdminAuthenticator"]


class AdminAuthenticator:
    """
    HMAC-based authenticator for admin API.

    Generates signature headers for authenticating admin requests.
    """

    def __init__(self, secret_key: str) -> None:
        """
        Initialize authenticator.

        Args:
            secret_key: Admin secret key for HMAC signing
        """
        self.secret_key = secret_key

    def sign_request(
        self,
        method: str,
        path: str,
        body: str = "",
    ) -> dict[str, str]:
        """
        Generate signature headers for request.

        The signature is calculated as:
        HMAC-SHA256(secret_key, timestamp + method + path + body)

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: Request path (e.g., "/api/v1/admin/users")
            body: Request body as string (typically JSON)

        Returns:
            Dictionary of headers to include in request:
            {
                "X-Signature": "hex_signature",
                "X-Timestamp": "milliseconds",
                "Content-Type": "application/json"
            }

        Example:
            >>> auth = AdminAuthenticator("secret-key")
            >>> headers = auth.sign_request("POST", "/api/v1/admin/users", '{"user_id":123}')
            >>> headers["X-Signature"]
            'a1b2c3...'
        """
        # Get current timestamp in milliseconds
        timestamp = str(int(time.time() * 1000))

        # Build payload: timestamp + method + path + body
        payload = f"{timestamp}{method}{path}{body}"

        # Calculate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Return headers
        return {
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "Content-Type": "application/json",
        }

    def verify_timestamp(self, timestamp: str, max_age_seconds: int = 300) -> bool:
        """
        Verify timestamp is not too old.

        Args:
            timestamp: Timestamp in milliseconds
            max_age_seconds: Maximum age in seconds (default: 5 minutes)

        Returns:
            True if timestamp is valid, False otherwise

        Example:
            >>> auth = AdminAuthenticator("secret-key")
            >>> auth.verify_timestamp("1619000000000")  # Old timestamp
            False
        """
        try:
            request_time = int(timestamp) / 1000  # Convert to seconds
            current_time = time.time()
            age = current_time - request_time

            return 0 <= age <= max_age_seconds
        except (ValueError, TypeError):
            return False

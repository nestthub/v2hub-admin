# V2Hub Admin — Admin Extension for VPN Subscription API

Admin extension for V2Hub, providing privileged operations for user, provider, and IP management through HMAC-SHA256 authentication.

### 🌐 Part of the [V2Hub Ecosystem](https://github.com/nestthub/nestthub/blob/main/ecosystems/v2hub/README.md)

This package is one component of V2Hub — see the full project overview, architecture, and all related repositories.

## Features

- 🔐 **HMAC Authentication** (SHA-256 signing)
- 👤 **User Management API** (user CRUD)
- 🤝 **Provider Management API** (provider CRUD, status, URL/name updates, token refresh)
- 🔑 **Provider Authorization API** (approve/reject provider access to a user's subscriptions)
- 📊 **Usage Statistics API** (aggregated stats by date range or period)
- 🚫 **IP Ban System**
- ✅ **Whitelist Management**
- 🔄 **Async & Sync clients**
- 📦 Built on top of `v2hub`
- 🛡️ Fully typed (type hints + Pydantic)

---

## Installation

```bash
pip install v2hub-admin
```

---

## Quick Start

## Async Usage

```python
from v2hub_admin import AsyncAdminClient

async with AsyncAdminClient(
    base_url="https://api.example.com",
    secret_key="your-hmac-secret"
) as admin:
    user = await admin.get_user(12345)
    print(user)
```

---

## Sync Usage

```python
from v2hub_admin import AdminClient

with AdminClient(
    base_url="https://api.example.com",
    secret_key="your-hmac-secret"
) as admin:
    user = admin.get_user(12345)
    print(user)
```

---

# Admin API

## 👤 User Management

```python
admin.create_user(user_id: int)
admin.get_user(user_id: int)
admin.delete_user(user_id: int)
admin.set_user_status(user_id: int, is_active: bool)
admin.refresh_token(user_id: int)
```

### Example

```python
user = admin.create_user(12345)
print(user.api_token)

user = admin.set_user_status(12345, False)
print(user.is_active)
```

---

## 🤝 Provider Management

```python
admin.create_provider(owner_hash: str, provider_name: str, provider_url: str | None = None)
admin.get_provider(provider_hash: str)
admin.get_providers()
admin.delete_provider(provider_hash: str)
admin.set_provider_status(provider_hash: str, is_active: bool)
admin.update_provider_url(provider_hash: str, provider_url: str | None)
admin.update_provider_name(provider_hash: str, provider_name: str)
admin.refresh_provider_token(provider_hash: str)
```

Providers are external services (e.g. bots, resellers) that manage subscriptions on behalf of end-users via `v2hub`'s `as_provider_for_user_id=` argument. This section covers the _admin_-side lifecycle of provider accounts themselves — creating them, rotating their tokens, enabling/disabling them.

### Example

```python
provider = admin.create_provider(
    owner_hash="a1b2c3d4e5f6...",
    provider_name="vpn123",
    provider_url="https://t.me/examplebot",
)
print(provider.provider_hash)
print(provider.api_token)

providers = admin.get_providers()
for name, provider_hash in providers.provider_hashes.items():
    print(name, provider_hash)

provider = admin.set_provider_status(provider.provider_hash, False)
print(provider.is_active)

result = admin.refresh_provider_token(provider.provider_hash)
print(result.new_api_token)
```

---

## 🔑 Provider Authorization Management

```python
admin.get_provider_authorization(provider_name: str, user_id: int)
admin.process_provider_authorization(user_id: int, provider_name: str, hmac: str | None = None)
admin.approve_provider_authorization(user_id: int, provider_name: str)
admin.reject_provider_authorization(user_id: int, provider_name: str)
```

Providers request access to manage a specific user's subscriptions via an HMAC-signed connection invite. This section covers the admin-side authorization handshake: inspecting the current state, processing an incoming request, and approving or rejecting it.

The typical flow is:

1. A provider issues a connection invite to a user, producing an `hmac`.
2. The invite is submitted via `process_provider_authorization(user_id, provider_name, hmac)`, creating a `PENDING` authorization.
3. An admin approves or rejects it with `approve_provider_authorization` / `reject_provider_authorization`.
4. `get_provider_authorization` can be used at any point to check the current status.

### Example

```python
# Create/process an authorization from an issued HMAC
auth = admin.process_provider_authorization(
    user_id=12345,
    provider_name="vpn123",
    hmac="a1b2c3d4e5f6...",
)
print(auth.status)  # "pending"

# Approve it (only PENDING authorizations can be approved)
auth = admin.approve_provider_authorization(user_id=12345, provider_name="vpn123")
print(auth.status)  # "approved"

# Check status later
auth = admin.get_provider_authorization("vpn123", 12345)
print(auth.status)

# Reject/revoke access
admin.reject_provider_authorization(user_id=12345, provider_name="vpn123")
```

> **Note:** `approve_provider_authorization` and `reject_provider_authorization` only operate on `PENDING` authorizations and raise `ConflictError` otherwise — including when the server's provider-per-user limit has been reached.

---

## 🚫 IP Ban Management

```python
admin.ban_ip(ip_address: str, duration_seconds: int | None = None)
admin.unban_ip(ip_address: str)
admin.get_ban_status(ip_address: str)
admin.get_ban_list()
```

### Example

```python
ban = admin.ban_ip("192.168.1.100", duration_seconds=3600)
print(ban.banned_until)

status = admin.get_ban_status("192.168.1.100")
print(status.is_banned)
```

---

## ✅ Whitelist Management

```python
admin.add_to_whitelist(ip_address: str, description: str | None = None)
admin.remove_from_whitelist(ip_address: str)
admin.list_whitelist()
```

### Example

```python
admin.add_to_whitelist("10.0.0.0/24", description="Office network")

whitelist = admin.list_whitelist()
for entry in whitelist.entries:
    print(entry.ip_address, entry.description)
```

---

## 📊 Usage Statistics

```python
admin.get_stats(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    period: Literal["day", "week", "month"] | None = None,
)
```

Get aggregated API usage statistics. Pass an explicit `start_date`/`end_date` range, a predefined `period` (`"day"`, `"week"`, or `"month"`), or omit all arguments to use the API's default range.

### Example

```python
from datetime import datetime, timedelta

# Predefined period
stats = admin.get_stats(period="week")

# Explicit date range
stats = admin.get_stats(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
)
```

---

## ⚠️ Error Handling

All errors inherit from `v2hub`:

```python
from v2hub import VPNAPIError, AuthenticationError, AuthorizationError

try:
    admin.delete_user(12345)
except AuthenticationError:
    print("Invalid HMAC signature")
except AuthorizationError:
    print("No admin privileges")
except VPNAPIError as e:
    print(e)
```

---

## Development

```bash
pip install -e ".[dev]"
pytest
mypy src/
```

---

## Requirements

- Python >= 3.10
- v2hub >= 1.1.2

---

## Security Notes

⚠️ Important:

- Do not hardcode `secret_key` in source code
- Use environment variables / secret managers
- HTTPS only in production
- Rotate keys regularly
- The Admin API has full access to the system

---

---

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for release notes.

---

## License

MIT

## Author

nestt

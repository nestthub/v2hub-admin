# V2Hub Admin — Admin Extension for VPN Subscription API

## Admin-расширение для V2Hub, предоставляющее привилегированные операции управления пользователями и IP через HMAC-SHA256 аутентификацию.

## Features

- 🔐 **HMAC Authentication** (SHA-256 подпись)
- 👤 **User Management API** (CRUD пользователей)
- 🚫 **IP Ban System**
- ✅ **Whitelist Management**
- 🔄 **Async & Sync клиенты**
- 📦 Основан на `v2hub`
- 🛡️ Полная типизация (type hints + Pydantic)

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

## ⚠️ Error Handling

Все ошибки наследуются из `v2hub`:

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

- Python >= 3.9
- v2hub >= 1.0.0

---

## Security Notes

⚠️ Важно:

- Не храните secret_key в коде
- Используйте env / secret managers
- Только HTTPS в production
- Регулярно ротируйте ключи
- Admin API имеет полный доступ к системе

---

## License

MIT

---

## Author

nestt

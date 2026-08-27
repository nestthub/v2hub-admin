# Changelog

All notable changes to `v2hub-admin` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Reconstructed from the git history of [`nestthub/v2hub-admin`](https://github.com/nestthub/v2hub-admin).

## [Unreleased]

## [1.1.3] - 2026-08-27

### Added

- **Provider Authorization Management**: a new set of endpoints for
  managing the authorization handshake between a provider and a user.
  - `get_provider_authorization(provider_name, user_id)` — inspect the
    current authorization state.
  - `process_provider_authorization(user_id, provider_name, hmac=None)` —
    submit a connection-invite HMAC to create a `PENDING` authorization,
    or query an existing one without an HMAC.
  - `approve_provider_authorization(user_id, provider_name)` — approve a
    pending authorization.
  - `reject_provider_authorization(user_id, provider_name)` — reject a
    pending authorization.
  - Available on both `AsyncAdminClient` and `AdminClient`, with automatic
    retries via `@with_async_retry()`.
  - New models in `v2hub_admin.models`: `ProviderAuthorizationBaseRequest`,
    `ProviderAuthorizationRequest`, `ProviderAuthorizationDecisionRequest`,
    `ProviderAuthorizationInfoResponse`.
  - Documented in the README under "Provider Authorization Management".
  - Bumps the `v2hub` dependency floor to `>=1.1.2` (needed for
    `ProviderAuthorizationStatus`).
- Full test coverage for the new endpoints: HTTP-level tests for
  `AsyncAdminClient`, delegation tests for the sync `AdminClient`, and
  isolated Pydantic model tests.

### Fixed

- Fixed `_request()` appending an empty `?` when no query parameters were
  provided.
- Fixed duplicate `ProviderAuthorization*` entries in `models.__all__`.
- Corrected provider authorization docstrings to reference `ConflictError`.
- Fixed `ProviderAuthorizationInfoResponse` import to use the public
  `v2hub_admin.models` package.

### Documentation

- Added a "Provider Authorization Management" section to `README.md`,
  covering the approve/reject flow and the `PENDING`-only precondition.
- Added a module docstring and fuller field/class docstrings to
  `provider_authorization.py`, matching the other model modules.

---

## [1.1.2] - 2026-08-16

### Added

- **Usage Statistics API**: `get_stats(start_date=None, end_date=None,
period=None)` on both clients, returning aggregated `StatsResponse` /
  `GeneralStats` (total users, new users, new subscriptions). Accepts
  either an explicit date range or a predefined `period`
  (`"day"`/`"week"`/`"month"`), or no arguments for the API's default
  range.
- `_request()` gained a `params` argument for query-string parameters
  (URL-encoded, `None` values dropped), needed for the new stats
  endpoint's optional filters.
- New `v2hub_admin.models.stats` module with `GeneralStats` and
  `StatsResponse`.
- README: new "Usage Statistics" and "Provider Management" sections
  (the latter documents the provider CRUD API shipped in 1.1.0, which
  had not previously been documented in the README).

### Changed

- Bumped the `v2hub` dependency floor from `>=1.0.0` to `>=1.1.1`.
- Tidied up `_request()`'s docstring and removed a couple of now-redundant
  inline comments (e.g. `# Prepare body`, `# Make request with signature
headers`) left over from earlier iterations.

## [1.1.1] - 2026-08-09

### Changed

- Version bump only; no functional or documentation changes.

## [1.1.0] - 2026-08-09

_(Merged via PR #2, `feat/provider-management-api`.)_

### Added

- **Provider Management API** on both clients:
  - `create_provider(owner_hash, provider_name, provider_url=None)`
  - `get_provider(provider_hash)`
  - `get_providers()`
  - `delete_provider(provider_hash)`
  - `set_provider_status(provider_hash, is_active)`
  - `update_provider_url(provider_hash, provider_url)`
  - `update_provider_name(provider_hash, provider_name)`
  - `refresh_provider_token(provider_hash)`
- New model modules: `v2hub_admin.models.providers`,
  `v2hub_admin.models.access_lists`, `v2hub_admin.models.users`,
  `v2hub_admin.models.base` — the previously monolithic `models.py` was
  split into a `models/` package along these lines.
- New test suites: `tests/test_async_client_providers.py`,
  `tests/test_client_providers.py`.

## [1.0.3] - 2026-07-23

### Added

- CI workflow (`.github/workflows/ci.yml`) and PyPI publish workflow
  (`.github/workflows/publish.yml`).
- `py.typed` marker for downstream type checking; pre-commit config with
  `mypy`.
- Full test suite: `tests/test_async_client.py`, `tests/test_auth.py`,
  `tests/test_client.py`, `tests/test_models.py`,
  `tests/test_public_api.py`.
- Raised `requires-python` from `>=3.9` to `>=3.10`.

### Fixed

- Package metadata lookup used the wrong distribution name
  (`version("v2hub")`/`metadata("v2hub")` instead of `"v2hub-admin"`),
  so `__version__`/`__author__` resolved against the wrong package. Fixed
  shortly after in a follow-up commit (`fix: correct package metadata
name`).

## [1.0.0] - 2026-05-03

### Added

- Initial release: HMAC-SHA256 request signing, async (`AsyncAdminClient`)
  and sync (`AdminClient`) clients, core data models, User Management API,
  IP Ban Management, and Whitelist Management.
- `feat(api): add __api_version__ and remove hardcoded version strings`
  (2026-05-18) — endpoint paths now build from a single
  `__api_version__` constant instead of hardcoded `"v1"` strings scattered
  through the client.

---

[Unreleased]: https://github.com/nestthub/v2hub-admin/compare/v1.1.3...main
[1.1.3]: https://github.com/nestthub/v2hub-admin/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/nestthub/v2hub-admin/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/nestthub/v2hub-admin/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/nestthub/v2hub-admin/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/nestthub/v2hub-admin/compare/v1.0.0...v1.0.3

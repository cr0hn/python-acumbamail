# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — 2026-08-03

### Fixed
- **BUG 1** — `manage_api_response_id()` crashed on `createList`'s real response shape
  `{"list_id": 456}` with `invalid literal for int() with base 10: 'list_id'` (a local
  regression that cast the dict *key* instead of the value). Now normalizes `'id'`,
  `'list_id'`, `'subscriber_id'`, `'campaign_id'`, and any key ending in `'_id'` by
  returning its *value*; keeps the legacy single-entry-dict-where-the-key-is-the-id
  form as a fallback (only when the value isn't int-castable); raises a clear
  `ValueError` naming the actual response shape instead of a raw Python exception.
- **BUG 2** — `batch_add_subscribers()` (sync and async) crashed with
  `int() argument must be a string, a bytes-like object or a real number, not 'dict'`
  when an email already existed in the list, even though the subscribers that
  *didn't* already exist were added successfully. `BatchSubscriberResult.from_api()`
  now tolerates heterogeneous item shapes (`{email: id}`, `{email: {"error": ...}}`,
  `{"error": {...}}`) item by item — one bad item never aborts the rest of the batch
  and never raises. `batch_add_subscribers()` now returns a `BatchAddSubscribersResult`
  (a plain list subclass — existing `email`/`subscriber_id` fields and iteration/
  indexing/`len()` behavior unchanged) with additive `.added`/`.already_existed`/
  `.failed` summary properties. The `batch-add` CLI command additively prints
  `status`/`error` per item alongside the existing `email`/`subscriber_id` fields.
- **BUG 6** — the rate-limit backoff logged "Waiting N seconds" but the HTTP read
  timeout was shorter than that wait, so the retried request died with
  `The read operation timed out` instead of completing. `_call_api()` (sync and
  async) now respects the `Retry-After` header when the API sends one (falling back
  to the previous `10 * retries` schedule otherwise), and raises the retried
  request's read timeout comfortably above the announced wait time. `AcumbamailClient`
  gained a `timeout` constructor param (default `30.0`, matching the async client).
- **BUG 3** — `get_inactive_subscribers()` silently accepted a `list_id` parameter,
  returned HTTP 200, and ignored it — verified against a nonexistent `list_id=99999999`,
  which still returned the account's full 805 inactive subscribers. This endpoint is
  **global to the account**, not scoped by list, and there is no server-side way to
  filter it. `get_inactive_subscribers()` (sync and async) now takes an explicit
  `list_id` parameter that, if passed, raises `AcumbamailValidationError` describing
  the limitation instead of pretending to filter. Cross-reference against
  `get_subscribers(list_id)` or `get_subscriber_details(list_id, email)` instead.
- **BUG 3b** — `acumbamail-openapi.yaml` documented the `reason` code in
  `get_inactive_subscribers(full_info=True)` backwards in two places (claimed
  `reason=3` was a hard bounce). Verified 2026-08-03 by cross-referencing 805 real
  inactive subscribers against the account's CSV exports: `reason=1` is the hard
  bounce (6 cases, none in any export) and `reason=3` is the voluntary unsubscribe
  (799 cases, 795 of them literally in the unsubscribes CSV). Fixed both spots in
  the OpenAPI spec. `InactiveSubscriber` gains a new `reason_label` field (an
  `InactiveReason` enum: `BOUNCE` / `UNSUBSCRIBED` / `UNKNOWN`) computed from the raw
  code; the raw `reason` int stays untouched for backwards compatibility.
- **BUG 4** — `subscribers list` only ever returned active subscribers, while
  `lists list`'s `subscribers_count` includes unsubscribes and bounces — comparing
  the two numbers looked like missing subscribers. Added a `--status` flag
  (`active` (default, unchanged behavior) / `inactive`) plus `--date-from`/
  `--date-to` to `subscribers list`.
  `--status active` requires `--list-id`; `--status inactive` is account-scoped and
  **rejects** `--list-id` with an error explaining why, because per BUG 3 the API
  cannot filter inactive subscribers by list. There is deliberately no `--status all`:
  it would add one list's actives to the whole account's inactives, and that total
  means nothing.
  The first attempt at this fix accepted `--list-id` alongside `--status inactive`
  and returned all 805 account-wide inactives as if they belonged to that list —
  reproducing inside our own CLI the exact deception BUG 3 fixed at the API layer.
  Caught by running it against a list with 16 subscribers and zero inactives.
- **BUG 5** — subscribers stuck in "not verified" (unconfirmed double opt-in) are
  invisible to `get_subscribers`, `search_subscriber`, `get_inactive_subscribers`,
  and the CSV exports — verified against a real case that only surfaced via
  `get_subscriber_details(list_id, email)` on its exact address. There is no way to
  *enumerate* them; the API only reveals the status per exact email. Documented the
  limitation in the `get_subscribers`/`search_subscriber` docstrings (sync and async)
  and added a `acumbamail subscribers check --email ... [--email ...] | --file
  emails.json --list-id ID` CLI command that reports the real status of each given
  email via `get_subscriber_details`, including "not verified" ones that no other
  command can see.

### Added
- `tests/test_utils.py`, `tests/test_rate_limit.py`, plus new cases in
  `tests/test_models.py`, `tests/test_client_new_methods.py`, and
  `tests/test_aclient_new_methods.py` covering BUGs 1, 2, and 6.
- New cases in `tests/test_models.py`, `tests/test_client_new_methods.py`,
  `tests/test_aclient_new_methods.py`, and `tests/test_cli.py` covering BUGs 3, 3b,
  4, and 5 (list_id rejection, reason_label mapping, `--status` combining, and
  `subscribers check` surfacing a "not verified" subscriber that `subscribers list`
  cannot see).
- `InactiveReason` enum (`acumbamail.models`), exported from the package root.

## [0.3.1] — 2026-05-19

### Added
- `AutomationClient.from_session(sessionid, csrftoken)` classmethod — creates a client from
  existing session cookies without requiring email/password login.
- `acumbamail automations login` CLI command — opens the real Chrome browser via Playwright,
  waits for the user to complete login, then saves `sessionid` and `csrftoken` cookies to
  `~/.config/acumbamail/session.json`. Subsequent automation commands reuse that session
  automatically (no credentials needed).
- `playwright>=1.40.0` added to main dependencies.
- `campaigns create` CLI command with `--html-file`/`--html`, `--from-email`, `--from-name`,
  `--scheduled-at`, and multiple `--list-id` support.
- Bundled `acumbamail-automations` Claude Code skill (install via `acumbamail install-skills`).

### Changed
- `get_automation_client()` in `cli/utils.py` now checks `~/.config/acumbamail/session.json`
  first; falls back to email/password programmatic login if not found.
- `close()` in `AutomationClient` is now safe even if `_client` was never set.
- Error message for missing credentials now directs user to run `acumbamail automations login`.
- `get_campaigns()` now correctly parses the `[{id_str: name}]` API response format.
- `Template.from_api()` no longer raises `KeyError` when `content` is absent from list responses.

### Fixed
- Removed real API token accidentally committed to `CLAUDE.md` and `tests/test_contracts.py`;
  both now read from `ACUMBAMAIL_TOKEN` env var. Git history purged.

### Docs
- Full README rewrite: hero banner, Getting Started, Automations as Code value proposition,
  download buttons for OpenAPI spec and Postman collection, TOC, n8n integration section.
- All documentation and bundled skills translated to English.
- CHANGELOG translated to English.

## [0.3.0] — 2026-05-18

### Added
- `AutomationClient`: new session-based client for the Acumbamail automation API
  (`/automation/api/`). Uses email+password auth (not API token).
- `Automation` and `AutomationNode` dataclasses.
- YAML-as-code support for automations: `load_yaml`, `validate_yaml`,
  `deploy_yaml`, `export_yaml` in `acumbamail.automation_yaml`.
- CLI command group `acumbamail automations` with subcommands:
  - `list` — list all automations as JSON
  - `deploy <file.yaml>` — idempotent deploy (create or update by name)
  - `export --id|--name` — export existing automation to YAML
  - `delete --id|--name` — delete automation
- Claude Code skill `acumbamail/data/skills/acumbamail-automations/SKILL.md`
  with full API reference and examples.
- Auth: `ACUMBAMAIL_EMAIL` + `ACUMBAMAIL_PASSWORD` env vars (or `--email`/`--password` flags).

### Notes
- `pyyaml` promoted from dev-only to main dependency.
- Automation API requires web session auth; public API token does not work.

## [2026-05-18] - Automations CLI: list, deploy, export, delete

### Added

- `acumbamail/cli/commands/automations.py`: new CLI module with 4 commands (`list`, `deploy`, `export`, `delete`) using `AutomationClient`
- `acumbamail/cli/utils.py`: `get_automation_client()` function that resolves credentials from `--email`/`--password` or `ACUMBAMAIL_EMAIL`/`ACUMBAMAIL_PASSWORD`
- `acumbamail/cli/main.py`: registered the `automations` group in the main CLI
- `acumbamail/__init__.py`: exported `AutomationClient`, `Automation`, `AutomationNode` in `__all__`
- `tests/test_automation_cli.py`: 8 unit tests (no network) covering all commands

## [2026-05-18] - Align version to 0.2.0, Optional[str] in type hints, explicit exports in __init__.py

### Changed

- `pyproject.toml`: version updated to `0.2.0`
- `acumbamail/__init__.py`: version updated to `0.2.0`; imports changed from wildcard (`*`) to explicit with full `__all__`
- `acumbamail/client.py`: parameters `str = None` and `Dict[str, Any] = None` corrected to `Optional[str]` and `Optional[Dict[str, Any]]` in `__init__`, `_call_api`, `add_subscriber`, `create_campaign`, `send_single_email`, `create_campaign_from_template` and `send_certified_email`
- `acumbamail/aclient.py`: same type hint changes as in `client.py` applied to the async client

## [2026-05-18] - Symmetric async/sync validations; warning in get_templates_by_name

### Added

- `AsyncAcumbamailClient.create_campaign`: symmetric validations matching the sync client:
  - `name` cannot be empty or whitespace-only
  - `subject` cannot be empty or whitespace-only
  - `content` cannot be empty or whitespace-only
  - `from_email` or `default_sender_email` required (already existed but reordered for consistency)
- `AsyncAcumbamailClient.send_single_email`: symmetric validations matching the sync client:
  - `to_email` must contain `@` (minimum email format)
  - `subject` cannot be empty or whitespace-only
  - `content` cannot be empty or whitespace-only
- `get_templates_by_name` (sync and async): emits `UserWarning` indicating that the endpoint
  is documented but returns 404 on the server (verified 2026-05-18); suggests
  using `get_templates()` and filtering on the client side
- 11 new tests: `TestAsyncCreateCampaignValidation`, `TestAsyncSendSingleEmailValidation`,
  `test_emits_user_warning` in sync and async

## [2026-05-18] - fix(examples): update all examples to current API

### Changed

- `examples/sync_example.py`: corrected env var to `ACUMBAMAIL_TOKEN`; flow updated to `get_lists`, `add_subscriber`, `get_subscribers`, `create_campaign` (with `*|UNSUBSCRIBE_URL|*`), `get_campaign_total_information`; removed `pre_header` (not present in current signature)
- `examples/async_example.py`: same changes as `sync_example.py` but with `AsyncAcumbamailClient` and `async with`; corrected env var
- `examples/campaign_analytics.py`: corrected env var; added `get_campaign_openers_by_browser` and `get_campaign_openers_by_os`; removed opener analysis by email (uses `get_campaign_openers` which is not in the list of available methods); simplified to use only real SDK methods
- `examples/bulk_operations.py`: completely rewritten; uses `batch_add_subscribers`, `search_subscriber` and `get_inactive_subscribers(full_info=True)` instead of individual loops; corrected env var
- `examples/ab_testing.py`: simplified; creates two campaigns with different subjects and compares `get_campaign_total_information`; added `*|UNSUBSCRIBE_URL|*` in content; removed dependency on non-existent `pre_header`; corrected env var
- `examples/automated_workflows.py`: rewritten; uses `create_list`, `batch_add_subscribers`, `create_campaign`, `get_campaign_total_information` and `get_list_webhook`/`config_list_webhook`; added `*|UNSUBSCRIBE_URL|*`; corrected env var
- `examples/error_handling.py`: rewritten; shows `AcumbamailValidationError` with invalid email and campaign without `*|UNSUBSCRIBE_URL|*`, `AcumbamailAPIError`, `AcumbamailRateLimitError`; removed `SafeAcumbamailClient` and `CircuitBreaker` (out of scope for the example); corrected env var
- `examples/example-001.py`: converted to minimal "Hello World" with `os.getenv("ACUMBAMAIL_TOKEN")` instead of hardcoded token
- `examples/README.md`: completely rewritten; documents all examples with real methods, warning about destructive operations, and note about `*|UNSUBSCRIBE_URL|*`

## [2026-05-18] - Migrate CI/CD from Poetry to uv with Trusted Publishing; update README

### Changed

- `.github/workflows/publish-to-pypi.yaml`: rewritten to use `uv` instead of Poetry
  - Split into two jobs: `test` and `publish`; Trusted Publishing (OIDC) via `pypa/gh-action-pypi-publish@release/v1`
  - Python updated from 3.11 to 3.13; uv via `astral-sh/setup-uv@v4`
- `README.md`: new CLI section, expanded Features, Core Methods with 25+ new methods, OpenAPI/Postman section

## [2026-05-18] - SDK improvements: new parameters and dead code removal

### Added

- `add_subscriber`: `double_optin: bool = False`, `update_subscriber: bool = False`
- `get_subscribers`: `block_index: int = 0`, `all_fields: bool = False`, `complete_json: bool = False`
- `get_list_subs_stats`: `block_index: int = 0`
- 22 new tests covering the new parameters (sync + async)

### Removed

- `utils.py`: removed 8 dead code functions

## [2026-05-18] - Tests for original SDK methods (pre-session)

### Added

- `tests/test_client_original.py`: 85 tests for the sync client (get_lists, create_list, get_subscribers, add_subscriber, delete_subscriber, create_campaign, send_single_email, get_templates, create_template, and more)
- `tests/test_aclient_original.py`: 80 tests for the async client (mirror of the sync client)

## [2026-05-18] - Quality tests and contract testing for the OpenAPI spec

### Added

- `tests/test_openapi_structure.py`: 16 structural validation tests for the YAML (no network)
  - Official OpenAPI 3.0.3 validation, tags, paths, schemas, internal $refs, counts
- `tests/test_openapi_coverage.py`: 7 spec vs SDK coverage tests (no network)
  - Verifies that all SDK endpoints are in the spec and vice versa
  - Documents SDK endpoints pending spec addition (`getTemplatesByName`)
- `tests/test_contracts.py`: 27 real contract tests against the API
  - Lists, subscribers, campaigns, templates, webhooks, SMTP
  - Marked with `@pytest.mark.contract`, excluded by default from `uv run pytest`
- `pyproject.toml` configuration: `contract` marker + `addopts = "-m 'not contract'"`

### Fixed

- `acumbamail-openapi.yaml`: corrected `ListStatsResponse` schema
  - Removed field `campaigns_sent` (the real API does not return it)
  - Added real fields: `spam_subscribers`, `name`, `create_date`
  - `campaigns_sent` was required in the spec but never appears in real responses

### Discovered (API quirks documented by contract testing)

- `getCampaigns`: returns a list of dicts `{campaign_id_str: campaign_name}`, NOT a list of objects with an `id` field
- `getCampaignOpenersByBrowser` / `getCampaignOpenersByOs`: return `[]` (empty list) when there are no openers, not `{}` (empty dict)
- `getTemplatesByName`: present in the SDK but not documented in the spec (pending)

## [2026-05-18] - Complete OpenAPI spec for the Acumbamail API

### Added

- Created `acumbamail-openapi.yaml`: complete OpenAPI 3.0.3 specification for the Acumbamail API
- 47 endpoints documented grouped into 6 tags: Lists, Subscribers, Campaigns, Templates, SMTP, Webhooks
- Reusable schemas: `AuthFields`, `ListInfo`, `SubscriberDetails`, `InactiveSubscriberFull`, `CampaignTotalInfo`, `CampaignClick`, `CampaignOpener`, `SMTPWebhookInfo`, `ListWebhookInfo`, etc.
- Real examples in schemas and responses
- Documentation of special behaviors: known bug in `batchDeleteSubscribers` (HTTP 500), uppercase `Creditos` key in `getCreditsSMTP`, `template_id` as string in `duplicateTemplate`, SMTP activation requirement for send endpoints
- Extension `x-rate-limit: "10 requests/minute"` on each operation
- Full descriptions for all HTTP response codes (200, 201, 400, 401, 404, 429, 500)

## [2026-05-18] - Complete Postman collection with all endpoints

### Added

- Updated `Acumbamail.postman_collection.json` with all API endpoints:
  - **Subscribers** (21 endpoints): getLists, createList, deleteList, getListStats, getListFields, getFields, getForms, getListSegments, getListSubsStats, getMergeFields, getSubscribers, addSubscriber, deleteSubscriber, batchAddSubscribers, batchDeleteSubscribers, deleteAllSubscribers, unsubscribeSubscriber, getSubscriberDetails, searchSubscriber, getInactiveSubscribers, addMergeTag, getCreditsSMTP
  - **Campaigns** (17 endpoints): createCampaign, sendTemplateCampaign, getCampaigns, getCampaignBasicInformation, getCampaignTotalInformation, getCampaignClicks, getCampaignOpeners, getCampaignOpenersByBrowser, getCampaignOpenersByOs, getCampaignOpenersByCountries, getCampaignInformationByISP, getCampaignLinks, getCampaignSoftBounces, getStatsByDate, getTemplates, createTemplate, duplicateTemplate
  - **SMTP** (4 endpoints, new folder): sendOne, send, sendCertifiedEmail, getEmailStatus
  - **Webhooks** (4 endpoints, new folder): getSMTPWebhook, configSMTPWebhook, getListWebhook, configListWebhook
- Added `template_id` variable to collection variables
- All requests include `response_type: "json"` in the body
- Fixed incorrect URLs in existing requests (getListSegments, getListSubsStats were pointing to wrong endpoints)

## [2026-05-18] - CLI: subscriber, campaign and webhook commands

### Added

- Implemented `acumbamail/cli/commands/subscribers.py` with commands: `list`, `add`, `delete`, `search`, `unsubscribe`, `batch-add`
- Implemented `acumbamail/cli/commands/campaigns.py` with commands: `list`, `info`, `stats`
- Implemented `acumbamail/cli/commands/webhooks.py` with commands: `smtp-get`, `smtp-config`, `list-get`, `list-config`
- Added 13 TDD tests in `tests/test_cli.py` (classes `TestSubscribersCommands`, `TestCampaignsCommands`, `TestWebhooksCommands`) — total 118 tests passing

## [2026-05-18] - CLI: list commands and initial main.py

### Added

- Created `acumbamail/cli/main.py` with the main Typer application and support for the global `--token` option
- Created `acumbamail/cli/commands/lists.py` with commands: `list`, `create`, `delete`, `stats`
- Created placeholder files `acumbamail/cli/commands/subscribers.py`, `campaigns.py`, `webhooks.py`
- Added 4 tests in `tests/test_cli.py` (class `TestListsCommands`) — total 105 tests passing

## [2026-05-18] - New methods in AsyncAcumbamailClient and async tests

### Added

- Added 22 new methods to the async client `AsyncAcumbamailClient` in `acumbamail/aclient.py`, equivalent to those in the sync client:
  - **Subscribers**: `add_merge_tag`, `batch_add_subscribers`, `batch_delete_subscribers`, `delete_all_subscribers`, `delete_list`, `get_smtp_credits`, `get_fields`, `get_forms`, `get_inactive_subscribers`, `get_subscriber_details`, `search_subscriber`, `unsubscribe_subscriber`
  - **Campaigns**: `send_template_campaign`, `duplicate_template`, `get_campaign_openers_by_countries`, `get_templates_by_name`
  - **SMTP**: `send_emails`, `send_certified_email`, `get_email_status`
  - **Webhooks**: `get_smtp_webhook`, `get_list_webhook`, `config_smtp_webhook`, `config_list_webhook`
- Added imports for `BatchSubscriberResult`, `SubscriberDetails`, `InactiveSubscriber`, `SMTPWebhook`, `ListWebhook` to the `.models` import block in `aclient.py`
- Created `tests/test_aclient_new_methods.py` with 43 async tests covering all new methods

## [2026-05-18] - New methods in AcumbamailClient

### Added

- Added 28 new methods to the sync client `AcumbamailClient` in `acumbamail/client.py`:
  - **Subscribers**: `add_merge_tag`, `batch_add_subscribers`, `batch_delete_subscribers`, `delete_all_subscribers`, `delete_list`, `get_smtp_credits`, `get_fields`, `get_forms`, `get_inactive_subscribers`, `get_subscriber_details`, `search_subscriber`, `unsubscribe_subscriber`
  - **Campaigns**: `send_template_campaign`, `duplicate_template`, `get_campaign_openers_by_countries`, `get_templates_by_name`
  - **SMTP**: `send_emails`, `send_certified_email`, `get_email_status`
  - **Webhooks**: `get_smtp_webhook`, `get_list_webhook`, `config_smtp_webhook`, `config_list_webhook`
- Added imports for `BatchSubscriberResult`, `SubscriberDetails`, `InactiveSubscriber`, `SMTPWebhook`, `ListWebhook` to the `.models` import block in `client.py`

## [2026-05-18] - New models

### Added

- Added 5 new dataclasses in `acumbamail/models.py`:
  - `SubscriberDetails`: full subscriber data (from `getSubscriberDetails` and `searchSubscriber`), with extra fields in `fields`
  - `InactiveSubscriber`: inactive subscriber (from `getInactiveSubscribers`), with optional `reason` and `reason_date`
  - `SMTPWebhook`: SMTP webhook configuration (from `getSMTPWebhook`)
  - `ListWebhook`: list webhook configuration (from `getListWebhook`), with `subscribes` and `unsubscribes`
  - `BatchSubscriberResult`: bulk subscription result (from `batchAddSubscribers`)
- Updated `__all__` with the new models

## [2026-05-18]

### Changed

- Migrated dependency management from Poetry to uv
- Minimum Python version raised from 3.11 to 3.13
- Changed build backend from `poetry-core` to `hatchling`
- Removed `poetry.lock`, generated `uv.lock`

## [0.1.0] - 2024-03-21

### Added

- Initial release
- Basic plugin system
- OpenAPI importer plugin
- JWT tester plugin
- HTML reporter plugin
- Configuration system
- Progress tracking
- Storage backend system

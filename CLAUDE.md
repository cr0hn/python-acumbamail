# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python SDK + CLI for the [Acumbamail](https://acumbamail.com) email marketing API. Sync (`AcumbamailClient`) and async (`AsyncAcumbamailClient`) clients, plus the `acumbamail` CLI command.

## Development Setup

```bash
uv sync                          # install deps (includes typer, httpx)
uv run pytest                    # run all tests
uv run pytest tests/test_cli.py::TestListsCommands -v   # single class
uv run acumbamail --help         # verify CLI works
uv build --wheel                 # build distribution
```

## Architecture

```
acumbamail/
├── client.py       # Sync client — httpx.Client per call
├── aclient.py      # Async client — shared httpx.AsyncClient (async context manager or .close())
├── models.py       # Dataclasses with from_api() classmethods
├── exceptions.py   # AcumbamailError → APIError, RateLimitError, ValidationError
├── utils.py        # manage_api_response_id() — normalizes int IDs from varied response shapes
├── data/
│   └── skills/acumbamail-cli/SKILL.md   # bundled Claude Code skill (shipped in wheel)
└── cli/
    ├── main.py                  # Typer app, registers all groups + install-skills
    ├── utils.py                 # get_client(), print_json(), handle_error()
    └── commands/
        ├── lists.py             # list, create, delete, stats
        ├── subscribers.py       # list, add, delete, search, unsubscribe, batch-add
        ├── campaigns.py         # list, info, stats
        ├── webhooks.py          # smtp-get/config, list-get/config
        └── install_skills.py    # install-skills [-g]
```

**Key patterns:**
- All API calls go through `_call_api(endpoint, data)` — injects `auth_token`+`response_type: json`, retries 429 with backoff (3× at 10s·retry).
- Models: `from_api(data)` parses API dicts; `to_api_payload()` for write ops (Campaign).
- Campaigns require `*|UNSUBSCRIBE_URL|*` in content — validated before calling API.
- `create_list()` requires `default_sender_email` set on client.
- `utils.py` only exports `manage_api_response_id()` — all other helpers were dead code and removed.
- `get_templates_by_name()` emits `UserWarning` — the endpoint is documented but returns 404 server-side.
- CLI: auth via `ACUMBAMAIL_TOKEN` env var or `--token` flag. All output JSON to stdout, errors to stderr + exit 1.
- New CLI commands must declare their own `--token` Option with `envvar="ACUMBAMAIL_TOKEN"` — the root callback propagates it via `os.environ` but Typer subcommands need their own declaration.

## Spec & Collection

- `acumbamail-openapi.yaml` — OpenAPI 3.0.3, 48 endpoints, schemas reutilizables, ejemplos reales
- `Acumbamail.postman_collection.json` — 47 endpoints en 4 folders (Subscribers, Campaigns, SMTP, Webhooks)

## API Implementation Coverage

All endpoints implemented. Intentionally excluded: SMS. Known broken/missing:
- `batchDeleteSubscribers` — API returns HTTP 500 (server bug, implemented anyway)
- `getTemplatesByName` — endpoint returns 404 (not implemented server-side)
- SMTP `send`, `sendCertifiedEmail`, `getEmailStatus` — require SMTP plan activation

## API Quirks (discovered via live testing)

| Endpoint | Quirk |
|----------|-------|
| `getCreditsSMTP` | Returns `{"Creditos": int}` — capital C |
| `duplicateTemplate` | Returns `{"template_id": "123"}` — ID as string |
| `getInactiveSubscribers` | `full_info=0` → `[["email"]]`; `full_info=1` → `[{"reason": int, "reason_date": "YYYY/MM/DD HH:MM:SS", "email": str}]` |
| `getSubscriberDetails` | Returns `{"email@x.com": {...}}` — outer key is the email |
| `addSubscriber` with `complete_json=1` | Returns `{"email": "...", "id": int}` |
| `deleteSubscriber` | Returns `{"email": "..."}` not `{}` |
| `getFields` | Returns `{"field_name": "field_type"}` dict |
| `getSubscribers` | `status` param is int, not string |
| `getCampaigns` | Returns `[{"campaign_id_str": "campaign_name"}]`, not `[{id: int, ...}]` |
| `getCampaignOpenersByBrowser/Os` | Returns `[]` (empty list) when no openers, not `{}` |
| `getTemplatesByName` | Server always returns 404 despite being in official docs; SDK emits `UserWarning` |

## Models

| Model | Source endpoint | Key fields |
|-------|----------------|------------|
| `MailList` | getLists | id, name, subscribers_count, bounced_count |
| `Subscriber` | getSubscribers | email, list_id, is_active, fields |
| `SubscriberDetails` | getSubscriberDetails / searchSubscriber | id, email, status, create_date, list_id, fields (dict of extra keys) |
| `InactiveSubscriber` | getInactiveSubscribers | email, reason, reason_date |
| `Campaign` | getCampaigns / createCampaign | id, name, subject, content, from_email, list_ids |
| `CampaignTotalInformation` | getCampaignTotalInformation | total_delivered, opened, unique_clicks, hard_bounces, … |
| `Template` | getTemplates | id, name, content |
| `BatchSubscriberResult` | batchAddSubscribers | email, subscriber_id |
| `SMTPWebhook` | getSMTPWebhook | id, url, active, delivered, hard_bounces, … |
| `ListWebhook` | getListWebhook | id, url, active, subscribes, unsubscribes, … |

## Testing

Tests use `pytest-httpx` mocks — no real API calls. `asyncio_mode = "auto"` in `pyproject.toml`.

```bash
uv run pytest                   # 346 unit/structural tests (no network)
uv run pytest -m contract       # 27 contract tests against real API (needs ACUMBAMAIL_TOKEN)
uv run pytest -m "not contract" # explicit exclusion
```

```
tests/
├── test_models.py                  # dataclass parsing from raw API responses
├── test_client_new_methods.py      # sync client (all new methods)
├── test_client_original.py         # sync client (original/pre-session methods)
├── test_aclient_new_methods.py     # async client (mirrors sync tests)
├── test_aclient_original.py        # async client (original methods)
├── test_cli.py                     # CLI via typer.testing.CliRunner + unittest.mock
├── test_openapi_structure.py       # OpenAPI 3.0.3 structural validation (no network)
├── test_openapi_coverage.py        # spec vs SDK endpoint coverage (no network)
└── test_contracts.py               # real API contract tests (marker: contract)
```

## CLI

```bash
export ACUMBAMAIL_TOKEN=YOUR_TOKEN_HERE

acumbamail lists list
acumbamail lists create --name "Lista" --sender-email x@x.com
acumbamail subscribers batch-add --list-id 1138335 --file subs.json
acumbamail campaigns stats --campaign-id 999
acumbamail webhooks list-config --list-id 1138335 --url https://... --subscribes --active

# Install Claude Code skill (teaches Claude how to use this CLI)
acumbamail install-skills        # → .claude/skills/acumbamail-cli/
acumbamail install-skills -g     # → ~/.claude/skills/acumbamail-cli/
```

Output is always JSON. Use `jq` for filtering: `acumbamail lists list | jq '.[].id'`

## Test Credentials

- Auth token: `YOUR_TOKEN_HERE`
- Test list ID: `1138335`

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python SDK for the [Acumbamail](https://acumbamail.com) email marketing API. Provides both synchronous (`AcumbamailClient`) and asynchronous (`AsyncAcumbamailClient`) clients.

## Development Setup

```bash
# Install dependencies
uv sync

# Run a script/test manually
uv run python examples/sync_example.py

# Run a single test
uv run python -m pytest tests/test_client.py::TestClassName::test_method -v
```

## Architecture

The SDK mirrors Acumbamail's REST API (base: `https://acumbamail.com/api/1/<endpoint>/`, always POST with JSON body).

```
acumbamail/
├── client.py      # Sync client (AcumbamailClient) — httpx.Client per call
├── aclient.py     # Async client (AsyncAcumbamailClient) — shared httpx.AsyncClient via context manager
├── models.py      # Dataclasses: MailList, Subscriber, Campaign, Template, CampaignTotalInformation, etc.
├── exceptions.py  # Exception hierarchy: AcumbamailError → AcumbamailAPIError, AcumbamailRateLimitError, AcumbamailValidationError
└── utils.py       # manage_api_response_id() — extracts int ID from various API response shapes
```

**Key patterns:**
- All API calls go through `_call_api(endpoint, data)` which injects `auth_token` and `response_type: json`, handles 429 with exponential backoff (3 retries, 10s × retry).
- `AsyncAcumbamailClient` must be used as an async context manager (`async with`) or `.close()` must be called. The sync client opens/closes httpx per request.
- Models have `from_api(data)` classmethods and `to_api_payload()` where write operations are needed.
- Campaigns require `*|UNSUBSCRIBE_URL|*` in content — enforced at SDK level before the API call.
- `create_list()` requires `default_sender_email` set on the client.

## API Reference

The Postman collection (`Acumbamail.postman_collection.json`) in the repo root is the authoritative reference for endpoint names and parameters. The official docs are at https://acumbamail.com/apidoc/ (requires login).

## Testing

```bash
# Ejecutar todos los tests (usan mocks, sin llamadas reales a la API)
uv run pytest

# Un test concreto
uv run pytest tests/test_client_new_methods.py::TestBatchAddSubscribers -v

# Tests de modelos
uv run pytest tests/test_models.py -v

# Tests async
uv run pytest tests/test_aclient_new_methods.py -v
```

Tests con `pytest-httpx` — mocking de httpx. Para el cliente async se usa `pytest.mark.asyncio` con `asyncio_mode = "auto"` (configurado en `pyproject.toml`).

## CLI

Instalado automáticamente con el paquete como comando `acumbamail`:

```bash
export ACUMBAMAIL_TOKEN=<tu_token>

# Listas
acumbamail lists list
acumbamail lists create --name "Mi Lista" --sender-email sender@x.com
acumbamail lists stats --list-id 123

# Suscriptores
acumbamail subscribers list --list-id 123
acumbamail subscribers add --list-id 123 --email x@x.com
acumbamail subscribers search --query x@x.com
acumbamail subscribers batch-add --list-id 123 --file subs.json

# Campañas
acumbamail campaigns list
acumbamail campaigns stats --campaign-id 456

# Webhooks
acumbamail webhooks smtp-get
acumbamail webhooks list-config --list-id 123 --url https://... --subscribes --active
```

O con flag: `acumbamail --token <token> lists list`. Salida siempre JSON a stdout. Errores a stderr con exit code 1.

## Test Token & List

- Auth token for testing: `YOUR_TOKEN_HERE`
- Test list: ID `1138335` (https://acumbamail.com/app/list/1138335/)
- SMS endpoints are excluded from this SDK intentionally.

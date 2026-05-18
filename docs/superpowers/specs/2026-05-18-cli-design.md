# CLI Design — acumbamail

**Date:** 2026-05-18  
**Status:** Approved

## Goal

Add a `acumbamail` CLI to the SDK for scripting and automation use cases. Output is always JSON to stdout; errors go to stderr with exit code 1.

## Auth

Token resolution order (first wins):
1. `--token TOKEN` flag
2. `ACUMBAMAIL_TOKEN` environment variable

If neither is present, the CLI exits with an error message to stderr.

## File Structure

```
acumbamail/cli/
├── __init__.py
├── main.py               # Typer app, registers command groups
├── utils.py              # get_client(), print_json(), error()
└── commands/
    ├── __init__.py
    ├── lists.py
    ├── subscribers.py
    ├── campaigns.py
    └── webhooks.py
```

Entry point registered in `pyproject.toml`:
```toml
[project.scripts]
acumbamail = "acumbamail.cli.main:app"
```

## Dependency

`typer` added to `[project.dependencies]`.

## Commands

### Lists

| Command | Options | SDK call |
|---------|---------|----------|
| `lists list` | — | `get_lists()` |
| `lists create` | `--name`, `--sender-email`, `[--description]` | `create_list()` |
| `lists delete` | `--list-id` | `delete_list()` |
| `lists stats` | `--list-id` | `get_list_stats()` |

### Subscribers

| Command | Options | SDK call |
|---------|---------|----------|
| `subscribers list` | `--list-id` | `get_subscribers()` |
| `subscribers add` | `--list-id`, `--email`, `[--fields JSON]` | `add_subscriber()` |
| `subscribers delete` | `--list-id`, `--email` | `delete_subscriber()` |
| `subscribers search` | `--query` | `search_subscriber()` |
| `subscribers batch-add` | `--list-id`, `--file PATH` | `batch_add_subscribers()` |
| `subscribers unsubscribe` | `--list-id`, `--email` | `unsubscribe_subscriber()` |

`--fields` accepts inline JSON string: `'{"name": "John"}'`  
`--file` for batch-add accepts a JSON file: array of objects with at least `"email"`.

### Campaigns

| Command | Options | SDK call |
|---------|---------|----------|
| `campaigns list` | — | `get_campaigns()` |
| `campaigns info` | `--campaign-id` | `get_campaign_basic_information()` |
| `campaigns stats` | `--campaign-id` | `get_campaign_total_information()` |

### Webhooks

| Command | Options | SDK call |
|---------|---------|----------|
| `webhooks smtp-get` | — | `get_smtp_webhook()` |
| `webhooks smtp-config` | `--url`, `[--delivered]`, `[--hard-bounce]`, `[--soft-bounce]`, `[--complain]`, `[--opens]`, `[--click]`, `[--active/--no-active]` | `config_smtp_webhook()` |
| `webhooks list-get` | `--list-id` | `get_list_webhook()` |
| `webhooks list-config` | `--list-id`, `--url`, `[--subscribes]`, `[--unsubscribes]`, `[--hard-bounce]`, `[--soft-bounce]`, `[--complain]`, `[--opens]`, `[--click]`, `[--active/--no-active]` | `config_list_webhook()` |

## Output Format

All commands print JSON to stdout. Examples:

```bash
$ acumbamail lists list
[{"id": 123, "name": "Newsletter", "subscribers_count": 500}]

$ acumbamail subscribers add --list-id 123 --email x@x.com
{"email": "x@x.com", "list_id": 123}

$ acumbamail campaigns stats --campaign-id 456
{"total_delivered": 490, "opened": 120, "unique_clicks": 45, ...}
```

Errors:
```bash
$ acumbamail lists list
Error: ACUMBAMAIL_TOKEN not set and --token not provided
# exit code 1, output to stderr
```

## Error Handling

- `AcumbamailAPIError` → stderr message + exit 1
- `AcumbamailValidationError` → stderr message + exit 1
- `AcumbamailRateLimitError` → stderr message + exit 1
- JSON parse errors on `--fields` input → stderr + exit 1

## Testing

Tests in `tests/test_cli.py` using `typer.testing.CliRunner` to invoke commands without a real HTTP client. Mock `AcumbamailClient` or use `pytest-httpx`.

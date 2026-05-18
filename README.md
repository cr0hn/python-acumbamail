# acumbamail

[![PyPI version](https://img.shields.io/pypi/v/acumbamail.svg)](https://pypi.org/project/acumbamail/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/cr0hn/py-acumbamail/actions/workflows/publish-to-pypi.yaml/badge.svg)](https://github.com/cr0hn/py-acumbamail/actions)

Python SDK and CLI for the [Acumbamail](https://acumbamail.com) email marketing API. Provides synchronous and asynchronous clients with full coverage of the REST API, plus a `acumbamail` command-line tool for scripting and automation.

## Installation

```bash
pip install acumbamail
```

Requires Python 3.13+.

## Quick start

```python
from acumbamail import AcumbamailClient

client = AcumbamailClient(
    auth_token="your-token",
    default_sender_name="My Company",
    default_sender_email="hello@mycompany.com",
)

# Create a list and add a subscriber
lst = client.create_list("Newsletter")
client.add_subscriber("user@example.com", lst.id, fields={"name": "Alice"})

# Send a campaign (content must include *|UNSUBSCRIBE_URL|*)
campaign = client.create_campaign(
    name="Welcome",
    subject="Thanks for subscribing!",
    content="<p>Hello! <a href='*|UNSUBSCRIBE_URL|*'>Unsubscribe</a></p>",
    list_ids=[lst.id],
)

# Check performance
stats = client.get_campaign_total_information(campaign.id)
print(f"Delivered: {stats.total_delivered}, Opened: {stats.opened}")
```

### Async usage

```python
import asyncio
from acumbamail import AsyncAcumbamailClient

async def main():
    async with AsyncAcumbamailClient(auth_token="your-token") as client:
        lists = await client.get_lists()
        stats = await client.get_campaign_total_information(campaign_id=123)
        print(f"Open rate: {stats.opened / stats.total_delivered:.1%}")

asyncio.run(main())
```

## CLI

The package ships with an `acumbamail` command that outputs JSON, suitable for shell scripting and CI pipelines.

```bash
export ACUMBAMAIL_TOKEN=your-token

# Lists
acumbamail lists list
acumbamail lists create --name "Newsletter" --sender-email hello@mycompany.com
acumbamail lists stats --list-id 123

# Subscribers
acumbamail subscribers list --list-id 123
acumbamail subscribers add --list-id 123 --email user@example.com
acumbamail subscribers search --query user@example.com
acumbamail subscribers batch-add --list-id 123 --file subscribers.json

# Campaigns
acumbamail campaigns list
acumbamail campaigns stats --campaign-id 456

# Webhooks
acumbamail webhooks smtp-get
acumbamail webhooks list-config --list-id 123 --url https://myapp.com/hook --subscribes --active
```

Use `--token <token>` as an alternative to the environment variable. All commands accept `--help`.

### Claude Code skill

If you use Claude Code, install the bundled skill so Claude understands the CLI:

```bash
acumbamail install-skills      # project-local  → .claude/skills/acumbamail-cli/
acumbamail install-skills -g   # user-global    → ~/.claude/skills/acumbamail-cli/
```

## Features

- Synchronous (`AcumbamailClient`) and asynchronous (`AsyncAcumbamailClient`) clients
- Complete API coverage — 48 endpoints across lists, subscribers, campaigns, templates, SMTP and webhooks
- Built on [httpx](https://www.python-httpx.org/) with automatic 429 retry and exponential backoff
- Typed models for every response (`MailList`, `Subscriber`, `Campaign`, `CampaignTotalInformation`, `SMTPWebhook`, …)
- `acumbamail` CLI with JSON output for scripting
- [OpenAPI 3.0.3 specification](acumbamail-openapi.yaml) and [Postman collection](Acumbamail.postman_collection.json) included

## Configuration

```python
client = AcumbamailClient(
    auth_token="your-token",           # required
    default_sender_name="My Company",  # used when from_name is not passed
    default_sender_email="hello@mycompany.com",  # required for create_list / create_campaign
    sender_company="My Company Inc.",  # stored in list metadata
    sender_country="ES",               # ISO country code, default "ES"
)
```

`AsyncAcumbamailClient` accepts the same parameters plus `timeout: float = 30.0`.

## API reference

### Mailing lists

| Method | Description |
|--------|-------------|
| `get_lists()` | All lists with subscriber counts |
| `create_list(name, description)` | Create a list |
| `delete_list(list_id)` | Delete a list |
| `get_list_stats(list_id)` | Stats dict (subscribers, bounces, …) |
| `get_fields(list_id)` | `{field_name: field_type}` mapping |
| `add_merge_tag(list_id, field_name, field_type)` | Add a custom field |

### Subscribers

| Method | Description |
|--------|-------------|
| `get_subscribers(list_id, block_index, all_fields, complete_json)` | Paginated subscriber list |
| `add_subscriber(email, list_id, fields, double_optin, update_subscriber)` | Add one subscriber |
| `delete_subscriber(email, list_id)` | Permanently remove |
| `unsubscribe_subscriber(list_id, email)` | Mark as unsubscribed without deleting |
| `batch_add_subscribers(list_id, subscribers_data, update_subscriber)` | Bulk add |
| `batch_delete_subscribers(list_id, email_list)` | Bulk delete |
| `delete_all_subscribers(list_id)` | Remove all (background process) |
| `get_subscriber_details(list_id, subscriber_email)` | Full subscriber record |
| `search_subscriber(query)` | Search across all lists |
| `get_inactive_subscribers(date_from, date_to, full_info)` | Inactive subscribers in a date range |

### Campaigns

| Method | Description |
|--------|-------------|
| `create_campaign(name, subject, content, list_ids, ...)` | Create and send |
| `send_template_campaign(name, subject, template_id, list_ids, ...)` | Send from a saved template |
| `get_campaigns(complete_json)` | List all campaigns |
| `get_campaign_basic_information(campaign_id)` | Name, subject, status |
| `get_campaign_total_information(campaign_id)` | Full stats (`CampaignTotalInformation`) |
| `get_campaign_clicks(campaign_id)` | Per-URL click data |
| `get_campaign_openers(campaign_id)` | Per-subscriber open data |
| `get_campaign_openers_by_browser(campaign_id)` | Opens grouped by browser |
| `get_campaign_openers_by_os(campaign_id)` | Opens grouped by OS |
| `get_campaign_openers_by_countries(campaign_id)` | Opens grouped by country |
| `get_campaign_soft_bounces(campaign_id)` | Soft bounce records |
| `get_stats_by_date(list_id, date_from, date_to)` | Aggregate daily stats |

`create_campaign` key parameters: `scheduled_at` (datetime), `tracking_enabled` (bool), `tracking_domain` (str), `https` (bool). Content **must** include `*|UNSUBSCRIBE_URL|*`.

### Templates

| Method | Description |
|--------|-------------|
| `get_templates()` | All templates |
| `create_template(template_name, html_content, subject, custom_category)` | Create a template |
| `duplicate_template(template_name, origin_template_id)` | Clone a template |

### SMTP transactional

> Requires SMTP plan activation in your Acumbamail account.

| Method | Description |
|--------|-------------|
| `send_single_email(to_email, subject, content, ...)` | One transactional email |
| `send_emails(messages)` | Batch transactional emails |
| `send_certified_email(to_email, subject, content, ...)` | Certified email |
| `get_email_status(email_key)` | Delivery status |
| `get_smtp_credits()` | Remaining credits |

### Webhooks

| Method | Description |
|--------|-------------|
| `get_smtp_webhook()` | Current SMTP webhook config |
| `config_smtp_webhook(callback_url, ...)` | Set SMTP webhook |
| `get_list_webhook(list_id)` | Current list webhook config |
| `config_list_webhook(list_id, callback_url, ...)` | Set list webhook |

## Error handling

```python
from acumbamail import (
    AcumbamailError,          # base class
    AcumbamailValidationError, # bad arguments (400)
    AcumbamailAPIError,        # HTTP errors (4xx/5xx)
    AcumbamailRateLimitError,  # 429, retried automatically up to 3 times
)

try:
    client.create_campaign(name="", subject="Hi", content="no unsubscribe", list_ids=[])
except AcumbamailValidationError as e:
    print(f"Bad request: {e}")
except AcumbamailRateLimitError:
    print("Rate limit hit — back off and retry")
except AcumbamailAPIError as e:
    print(f"API returned an error: {e}")
```

## Examples

Runnable examples are in the [`examples/`](examples/) directory:

| File | What it shows |
|------|--------------|
| `sync_example.py` | Basic synchronous workflow |
| `async_example.py` | Async workflow with `AsyncAcumbamailClient` |
| `campaign_analytics.py` | Open/click rates, browser and OS breakdown |
| `bulk_operations.py` | `batch_add_subscribers`, inactive subscriber cleanup |
| `ab_testing.py` | Two-variant campaign comparison |
| `automated_workflows.py` | List creation, bulk import, campaign, webhook setup |
| `error_handling.py` | Catching and handling every exception type |

```bash
export ACUMBAMAIL_TOKEN=your-token
python examples/sync_example.py
```

## Contributing

Contributions are welcome. Please open an issue before starting significant work so we can discuss the approach.

```bash
git clone https://github.com/cr0hn/py-acumbamail
cd py-acumbamail
uv sync
uv run pytest          # unit + structural tests (no network)
uv run pytest -m contract  # contract tests against the real API (requires ACUMBAMAIL_TOKEN)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## License

[MIT](LICENSE) © Daniel Garcia (cr0hn)

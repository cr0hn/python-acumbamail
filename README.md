<p align="center">
  <img src="https://raw.githubusercontent.com/cr0hn/python-acumbamail/main/assets/acumbamail-logo.svg" alt="Acumbamail" width="320">
</p>

<p align="center">
  <em>Complete Python SDK, CLI, and automation workflows for <a href="https://acumbamail.com">Acumbamail</a> email marketing.</em>
</p>

<p align="center">
<a href="https://pypi.org/project/acumbamail/"><img src="https://img.shields.io/pypi/v/acumbamail.svg" alt="PyPI version"></a>
<a href="https://pypi.org/project/acumbamail/"><img src="https://img.shields.io/pypi/pyversions/acumbamail.svg" alt="Python versions"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
<a href="https://github.com/cr0hn/python-acumbamail/actions/workflows/publish-to-pypi.yaml"><img src="https://github.com/cr0hn/python-acumbamail/actions/workflows/publish-to-pypi.yaml/badge.svg" alt="CI"></a>
<a href="https://pepy.tech/project/acumbamail"><img src="https://static.pepy.tech/badge/acumbamail/month" alt="Monthly downloads"></a>
</p>

<p align="center">
<a href="https://raw.githubusercontent.com/cr0hn/python-acumbamail/main/acumbamail-openapi.yaml"><img src="https://img.shields.io/badge/Download-OpenAPI%203.0.3-85EA2D?logo=openapiinitiative&logoColor=white" alt="Download OpenAPI spec"></a>
<a href="https://raw.githubusercontent.com/cr0hn/python-acumbamail/main/Acumbamail.postman_collection.json"><img src="https://img.shields.io/badge/Download-Postman%20Collection-FF6C37?logo=postman&logoColor=white" alt="Download Postman collection"></a>
</p>

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage](#usage)
  - [Python SDK](#python-sdk)
  - [CLI](#cli)
  - [Automations as Code](#automations-as-code)
- [API Reference](#api-reference)
  - [Mailing Lists](#mailing-lists)
  - [Subscribers](#subscribers)
  - [Campaigns](#campaigns)
  - [Templates](#templates)
  - [SMTP Transactional](#smtp-transactional)
  - [Webhooks](#webhooks)
- [Error Handling](#error-handling)
- [Claude Code Skill](#claude-code-skill)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

**acumbamail** is a Python SDK and CLI with complete coverage of the [Acumbamail](https://acumbamail.com) REST API. It provides **sync and async clients**, a **JSON-outputting CLI** for shell scripting and CI pipelines, and — uniquely — **automation workflows as YAML code** so you can version-control and deploy email sequences the same way you deploy software.

```python
>>> from acumbamail import AcumbamailClient
>>> client = AcumbamailClient(auth_token="...", default_sender_email="hello@company.com")
>>> lst = client.create_list("Newsletter")
>>> client.add_subscriber("user@example.com", lst.id, fields={"name": "Alice"})
>>> campaign = client.create_campaign(
...     name="Welcome", subject="Thanks for subscribing!",
...     content='<p>Hello!</p><a href="*|UNSUBSCRIBE_URL|*">Unsubscribe</a>',
...     list_ids=[lst.id],
... )
>>> stats = client.get_campaign_total_information(campaign.id)
>>> f"{stats.opened / stats.total_delivered:.1%} open rate"
'28.3% open rate'
```

## Features

- **Sync and async clients** — `AcumbamailClient` and `AsyncAcumbamailClient` share the same API surface; async client is an async context manager.
- **Full API coverage** — 48 endpoints across lists, subscribers, campaigns, templates, SMTP, and webhooks.
- **JSON CLI** — every command outputs JSON, piped straight into `jq` or CI scripts.
- **Automations as code** — define email sequences in YAML, deploy with `acumbamail automations deploy`. Version-controlled, idempotent, reviewable.
- **Automatic retry** — 429 responses are retried up to 3× with exponential backoff; no extra configuration needed.
- **Typed models** — every response is a typed dataclass (`MailList`, `Campaign`, `CampaignTotalInformation`, …).
- **OpenAPI 3.0.3 spec** and **Postman collection** included in the repository.
- **Claude Code skill** — install a bundled skill so AI assistants understand the full CLI and SDK.

## Installation

```bash
# Using pip
pip install acumbamail

# Using uv
uv add acumbamail

# CLI only (no Python import needed)
pipx install acumbamail
```

Requires Python 3.13+.

## Getting Started

**1. Get your API token** — log in to [acumbamail.com](https://acumbamail.com), go to **Settings → API**, and copy your token.

**2. Set the environment variable:**

```bash
export ACUMBAMAIL_TOKEN=your-token-here
```

**3. Create a list and send your first campaign:**

```python
from acumbamail import AcumbamailClient

client = AcumbamailClient(
    auth_token="your-token",
    default_sender_email="hello@mycompany.com",
    default_sender_name="My Company",
)

# Create a mailing list
lst = client.create_list("My Newsletter")
print(f"List created: {lst.id}")

# Add a subscriber
client.add_subscriber("alice@example.com", lst.id, fields={"nombre": "Alice"})

# Send your first campaign
campaign = client.create_campaign(
    name="First Campaign",
    subject="Hello from acumbamail!",
    content="""
        <h1>Hello *|FNAME|*!</h1>
        <p>Welcome to our newsletter.</p>
        <a href="*|UNSUBSCRIBE_URL|*">Unsubscribe</a>
    """,
    list_ids=[lst.id],
)
print(f"Campaign sent: {campaign.id}")

# Check results the next day
stats = client.get_campaign_total_information(campaign.id)
print(f"Delivered: {stats.total_delivered}, Opened: {stats.opened}")
```

Or with the CLI:

```console
$ acumbamail lists create --name "My Newsletter" --sender-email hello@mycompany.com
{"id": 1138335, "name": "My Newsletter"}

$ acumbamail subscribers add --list-id 1138335 --email alice@example.com
{"email": "alice@example.com", "list_id": 1138335}

$ acumbamail campaigns create \
    --name "First Campaign" --subject "Hello!" \
    --html '<h1>Hi!</h1><a href="*|UNSUBSCRIBE_URL|*">Unsubscribe</a>' \
    --list-id 1138335 --from-email hello@mycompany.com
{"id": 3294239, "name": "First Campaign", ...}
```

> [!TIP]
> Your sender email must be verified in Acumbamail before sending campaigns. Add it at **Settings → Verified senders**.

## Usage

### Python SDK

```python
from acumbamail import AcumbamailClient

client = AcumbamailClient(
    auth_token="your-token",
    default_sender_name="My Company",
    default_sender_email="hello@mycompany.com",
)

# Lists and subscribers
lists = client.get_lists()
client.add_subscriber("user@example.com", list_id=lists[0].id)
client.batch_add_subscribers(lists[0].id, [
    {"email": "a@example.com", "nombre": "Alice"},
    {"email": "b@example.com", "nombre": "Bob"},
])

# Campaigns
campaign = client.create_campaign(
    name="May Newsletter",
    subject="What's new this month",
    content='<h1>Hello *|FNAME|*</h1><a href="*|UNSUBSCRIBE_URL|*">Unsubscribe</a>',
    list_ids=[lists[0].id],
)

# Analytics
stats = client.get_campaign_total_information(campaign.id)
clicks = client.get_campaign_clicks(campaign.id)
openers = client.get_campaign_openers_by_browser(campaign.id)
```

<details>
<summary>Or use <code>async with AsyncAcumbamailClient</code>…</summary>

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

The async client is identical in API to the sync client. Use `async with` or call `.close()` manually.

</details>

### CLI

All commands output JSON. Pipe into `jq` for filtering.

```console
$ export ACUMBAMAIL_TOKEN=your-token

$ acumbamail lists list
[{"id": 1138335, "name": "Newsletter", "subscribers_count": 1200, ...}]

$ acumbamail subscribers batch-add --list-id 1138335 --file subscribers.json
[{"email": "a@x.com", "subscriber_id": 111}, ...]

$ acumbamail campaigns create \
    --name "May Newsletter" \
    --subject "What's new this month" \
    --html-file email.html \
    --list-id 1138335 \
    --from-email hello@mycompany.com
{"id": 3294239, "name": "May Newsletter", "subject": "What's new this month", ...}

$ acumbamail campaigns stats --campaign-id 3294239 | \
    jq '{open_rate: (.opened / .total_delivered * 100 | round | tostring + "%")}'
{"open_rate": "28%"}
```

<details>
<summary>All available commands…</summary>

```console
$ acumbamail lists list
$ acumbamail lists create --name "My List" --sender-email hello@mycompany.com
$ acumbamail lists delete --list-id 123
$ acumbamail lists stats --list-id 123

$ acumbamail subscribers list --list-id 123
$ acumbamail subscribers add --list-id 123 --email user@example.com
$ acumbamail subscribers delete --list-id 123 --email user@example.com
$ acumbamail subscribers search --query user@example.com
$ acumbamail subscribers unsubscribe --list-id 123 --email user@example.com
$ acumbamail subscribers batch-add --list-id 123 --file subscribers.json

$ acumbamail campaigns list
$ acumbamail campaigns create --name "..." --subject "..." --html-file email.html --list-id 123
$ acumbamail campaigns info --campaign-id 456
$ acumbamail campaigns stats --campaign-id 456

$ acumbamail webhooks smtp-get
$ acumbamail webhooks smtp-config --url https://myapp.com/hooks/smtp --delivered --active
$ acumbamail webhooks list-get --list-id 123
$ acumbamail webhooks list-config --list-id 123 --url https://myapp.com/hooks/list --subscribes --active

$ acumbamail automations login
$ acumbamail automations list
$ acumbamail automations deploy workflow.yaml
$ acumbamail automations export --name "welcome-sequence"
$ acumbamail automations delete --name "welcome-sequence"
```

Use `--token <token>` as an alternative to `ACUMBAMAIL_TOKEN`. Every command accepts `--help`.

</details>

### Automations as Code

Most email platforms treat automations as a GUI-only feature: you click through a visual editor, and the result lives exclusively in their cloud — invisible to Git, impossible to review in a PR, painful to replicate across accounts.

**acumbamail** takes a different approach. Your automation workflows live as YAML files in your repository, right next to your code. You deploy them with a single command, the same way you'd apply a Terraform plan or a Kubernetes manifest.

**What you get:**

- **Version control** — every change to a workflow goes through a commit. `git diff` shows exactly what changed between the old and new sequence.
- **Code review** — workflows are PR-reviewable. Your team can catch logic errors before a broken sequence goes out to thousands of subscribers.
- **Reproducibility** — recreate any automation on a new account or staging environment in seconds, from a file.
- **Idempotency** — deploying the same file twice is always safe. Acumbamail identifies workflows by `name`, replaces in place, and reports `"action": "updated"`.
- **Backup and recovery** — `acumbamail automations export` pulls any existing workflow back to YAML. Even automations built in the GUI can be exported, put under version control, and managed from that point on.

```yaml
# welcome-sequence.yaml  ← lives in your repo, reviewed in PRs
name: welcome-sequence
trigger:
  list_id: 1138335
  event: subscriber_added   # fires when someone joins the list

steps:
  - type: email_template
    subject: "Welcome aboard!"
    template_id: 8986619

  - type: delay
    wait: 3
    unit: days

  - type: email_template
    subject: "Getting started guide"
    template_id: 8986620

  - type: delay
    wait: 7
    unit: days

  # Branch on engagement: reward active subscribers, re-engage quiet ones
  - type: condition
    on_match:
      - type: email_template
        subject: "Special offer for active subscribers"
        template_id: 8986621
    on_no_match:
      - type: email_template
        subject: "We miss you — come back?"
        template_id: 8986622
```

```console
$ acumbamail automations login          # one-time: opens Chrome, saves session for 30 days
$ acumbamail automations deploy welcome-sequence.yaml
{"workflow_id": 36215, "action": "created", "active": false}

$ # Edit the YAML, redeploy — safe and idempotent
$ acumbamail automations deploy welcome-sequence.yaml
{"workflow_id": 36215, "action": "updated", "active": false}

$ # Pull an existing automation back to YAML (even ones built in the GUI)
$ acumbamail automations export --name "welcome-sequence" > welcome-sequence.yaml

$ acumbamail automations list | jq '[.[] | select(.active == true)]'
```

> [!NOTE]
> Automations use Acumbamail's web session (not the API token). Run `acumbamail automations login` once — the session lasts 30 days.

Supported step types: `email_template`, `delay`, `condition`, `until`, `webhook`, `update_field`, `move_to`.

## API Reference

### Mailing Lists

| Method | Description |
|--------|-------------|
| `get_lists()` | All lists with subscriber counts |
| `create_list(name, description)` | Create a list |
| `delete_list(list_id)` | Delete a list |
| `get_list_stats(list_id)` | Subscriber, bounce, and unsubscribe counts |
| `get_fields(list_id)` | `{field_name: field_type}` mapping |
| `add_merge_tag(list_id, field_name, field_type)` | Add a custom field |

### Subscribers

| Method | Description |
|--------|-------------|
| `get_subscribers(list_id, ...)` | Paginated subscriber list |
| `add_subscriber(email, list_id, fields, double_optin, update_subscriber)` | Add one subscriber |
| `delete_subscriber(email, list_id)` | Permanently remove |
| `unsubscribe_subscriber(list_id, email)` | Mark as unsubscribed without deleting |
| `batch_add_subscribers(list_id, subscribers_data, update_subscriber)` | Bulk add |
| `delete_all_subscribers(list_id)` | Remove all (background process) |
| `get_subscriber_details(list_id, subscriber_email)` | Full subscriber record |
| `search_subscriber(query)` | Search across all lists |
| `get_inactive_subscribers(list_id, date_from, date_to, full_info)` | Inactive subscribers in a date range |

### Campaigns

| Method | Description |
|--------|-------------|
| `create_campaign(name, subject, content, list_ids, scheduled_at, ...)` | Create and send (or schedule) |
| `send_template_campaign(name, subject, template_id, list_ids, ...)` | Send from a saved template |
| `get_campaigns()` | List all campaigns |
| `get_campaign_basic_information(campaign_id)` | Name, subject, status |
| `get_campaign_total_information(campaign_id)` | Full stats — `CampaignTotalInformation` |
| `get_campaign_clicks(campaign_id)` | Per-URL click data |
| `get_campaign_openers(campaign_id)` | Per-subscriber open data |
| `get_campaign_openers_by_browser(campaign_id)` | Opens grouped by browser |
| `get_campaign_openers_by_os(campaign_id)` | Opens grouped by OS |
| `get_campaign_openers_by_countries(campaign_id)` | Opens grouped by country |
| `get_campaign_soft_bounces(campaign_id)` | Soft bounce records |
| `get_stats_by_date(list_id, date_from, date_to)` | Aggregate stats for a list over a date range |

> [!IMPORTANT]
> Campaign HTML **must** include `*|UNSUBSCRIBE_URL|*` — the API rejects content without it. Merge tags `*|FNAME|*`, `*|LNAME|*`, `*|EMAIL|*`, and `*|FULLNAME|*` are also available.

### Templates

| Method | Description |
|--------|-------------|
| `get_templates()` | All templates |
| `create_template(template_name, html_content, subject)` | Create a template |
| `duplicate_template(template_name, origin_template_id)` | Clone a template |

### SMTP Transactional

> [!NOTE]
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

## Error Handling

```python
from acumbamail import (
    AcumbamailError,           # base class
    AcumbamailValidationError,  # bad arguments — 400 (e.g. missing UNSUBSCRIBE_URL)
    AcumbamailAPIError,         # HTTP errors — 4xx/5xx
    AcumbamailRateLimitError,   # 429 — retried automatically up to 3×
)

try:
    client.create_campaign(
        name="Test", subject="Hi",
        content="<p>No unsubscribe link here</p>",  # will raise
        list_ids=[123],
    )
except AcumbamailValidationError as e:
    print(f"Validation error: {e}")
except AcumbamailRateLimitError:
    print("Rate limited — the SDK already retried 3× with backoff")
except AcumbamailAPIError as e:
    print(f"API error: {e}")
```

## Claude Code Skill

If you use Claude Code, install the bundled skill so your AI assistant knows the complete CLI API and quirks:

```console
$ acumbamail install-skills      # project-local  → .claude/skills/
$ acumbamail install-skills -g   # user-global    → ~/.claude/skills/
```

Two skills are installed: `acumbamail-cli` (lists, subscribers, campaigns, webhooks, templates) and `acumbamail-automations` (YAML schema, deploy/export/delete workflows).

## Examples

Runnable examples are in [`examples/`](examples/):

| File | What it shows |
|------|--------------|
| `sync_example.py` | Basic synchronous workflow |
| `async_example.py` | Async workflow with `AsyncAcumbamailClient` |
| `campaign_analytics.py` | Open/click rates, browser and OS breakdown |
| `bulk_operations.py` | `batch_add_subscribers`, inactive subscriber cleanup |
| `ab_testing.py` | Two-variant campaign comparison |
| `automated_workflows.py` | List creation, bulk import, campaign, webhook setup |
| `error_handling.py` | Catching and handling every exception type |

```console
$ export ACUMBAMAIL_TOKEN=your-token
$ python examples/sync_example.py
```

## Contributing

Contributions are welcome. Please open an issue before starting significant work.

```bash
git clone https://github.com/cr0hn/python-acumbamail
cd python-acumbamail
uv sync
uv run pytest                  # unit + structural tests (no network)
uv run pytest -m contract      # contract tests against the real API (requires ACUMBAMAIL_TOKEN)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## License

[MIT](LICENSE) © Daniel Garcia (cr0hn)

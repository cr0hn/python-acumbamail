---
name: acumbamail-cli
description: Use when working with the Acumbamail CLI or Python SDK — managing lists, subscribers, campaigns, templates, and webhooks. Covers all CLI subcommands, SDK methods, authentication, known quirks and limitations discovered via real API testing.
---

# Acumbamail CLI & SDK

The `acumbamail` CLI and Python SDK manage Acumbamail email marketing. All CLI output is JSON on stdout; errors go to stderr with exit code 1.

## Authentication

```bash
export ACUMBAMAIL_TOKEN=your_token_here

# or per-command:
acumbamail --token YOUR_TOKEN lists list
```

```python
from acumbamail import AcumbamailClient
client = AcumbamailClient(
    auth_token="your_token",
    default_sender_email="sender@domain.com",   # required for campaigns
    default_sender_name="My Company",
)
```

---

## CLI Commands

### `lists` — Subscriber Lists

```bash
acumbamail lists list
# → [{"id": 123, "name": "Newsletter", "subscribers_count": 500, "bounced_count": 3, ...}]

acumbamail lists create --name "My List" --sender-email sender@example.com
acumbamail lists create --name "My List" --sender-email sender@example.com --description "Weekly"
# → {"id": 456, "name": "My List", "description": ""}

acumbamail lists delete --list-id 456
# → {"deleted": true, "list_id": 456}

acumbamail lists stats --list-id 123
# → {"total_subscribers": 500, "unsubscribed_subscribers": 12, "hard_bounced_subscribers": 3, ...}
```

### `subscribers` — Subscribers

```bash
acumbamail subscribers list --list-id 123
# → [{"email": "user@x.com", "list_id": 123, "is_active": true, "fields": {...}}, ...]

acumbamail subscribers add --list-id 123 --email user@example.com
acumbamail subscribers add --list-id 123 --email user@example.com --fields '{"nombre": "Juan"}'
# → {"email": "user@example.com", "list_id": 123}

acumbamail subscribers delete --list-id 123 --email user@example.com
# → {"deleted": true, "email": "user@example.com", "list_id": 123}

acumbamail subscribers search --query user@example.com
# → [{"email": "user@example.com", "status": "active", "list_id": 123, "id": 456}, ...]

acumbamail subscribers unsubscribe --list-id 123 --email user@example.com
# → {"unsubscribed": true, "email": "user@example.com", "list_id": 123}

# Bulk import from JSON: [{"email": "a@x.com"}, {"email": "b@x.com", "nombre": "Bob"}]
acumbamail subscribers batch-add --list-id 123 --file subs.json
acumbamail subscribers batch-add --list-id 123 --file subs.json --update  # update if already exists
# → [{"email": "a@x.com", "subscriber_id": 111}, ...]
```

### `campaigns` — Email Campaigns

```bash
# Create and send a campaign (immediate send if --scheduled-at is not specified)
acumbamail campaigns create \
  --name "Newsletter Mayo" \
  --subject "Novedades de este mes" \
  --html-file email.html \
  --list-id 1138335 \
  --from-email sender@domain.com \
  --from-name "Mi Empresa"
# → {"id": 3294239, "name": "...", "subject": "...", "from_email": "...", "list_ids": [...]}

# Inline HTML
acumbamail campaigns create --name "Aviso" --subject "Importante" \
  --html '<h1>Hola</h1><a href="*|UNSUBSCRIBE_URL|*">Baja</a>' \
  --list-id 1138335 --from-email sender@domain.com

# Schedule send
acumbamail campaigns create --name "Newsletter" --subject "..." \
  --html-file email.html --list-id 1138335 \
  --scheduled-at "2026-06-01 09:00"

# Multiple lists (repeat --list-id)
acumbamail campaigns create --name "Promo" --subject "Oferta" \
  --html-file promo.html --list-id 123 --list-id 456

# List campaigns — returns id and name ONLY (API limitation)
acumbamail campaigns list
# → [{"id": 3294239, "name": "Newsletter #1", "subject": "", "from_email": "", "list_ids": []}, ...]
# To see subject/from_email use: campaigns info

# Full detail of a campaign (subject, from_email, lists, status)
acumbamail campaigns info --campaign-id 3294239
# → {"status": "Sent", "name": "...", "subject": "...", "email_from": "...", "lists": [...]}

# Stats
acumbamail campaigns stats --campaign-id 3294239
# → {"total_delivered": 490, "opened": 120, "unique_clicks": 45, "hard_bounces": 8, ...}
```

**Required HTML — unsubscribe tag:**

```html
<!-- REQUIRED in all campaign HTML -->
<a href="*|UNSUBSCRIBE_URL|*">Darse de baja</a>
```

**Available merge tags:**

```
*|UNSUBSCRIBE_URL|*   → unsubscribe URL (the only one validated — fails if missing)
*|FNAME|*             → first name
*|LNAME|*             → last name
*|EMAIL|*             → subscriber email
*|FULLNAME|*          → full name
*|ARCHIVE_URL|*       → online version of the campaign
*|FORWARD_URL|*       → forward to a friend
```

The API accepts any `*|TAG|*` without validation — only `*|UNSUBSCRIBE_URL|*` is checked.

**Common errors in campaigns create:**
- `el HTML no contiene el tag de desuscripción` → add `*|UNSUBSCRIBE_URL|*`
- `el email del remitente no está verificado` → verify at https://acumbamail.com/app/account/senders/
- `from_email or default_sender_email is required` → add `--from-email`

**Campaign API limitations:**
- `campaigns list` only returns id+name (the API does not provide more in the listing)
- Campaigns cannot be **deleted** via API — only from the web panel
- Scheduled campaigns cannot be **cancelled** via API — only from the web panel
- `pre_header` and `tracking_domain` are accepted on creation but do NOT appear in `campaigns info`
- `send_single_email` requires an SMTP plan (returns 401 without it)

### `webhooks` — Webhooks

```bash
acumbamail webhooks smtp-get
acumbamail webhooks smtp-config --url https://myapp.com/hooks/smtp --delivered --hard-bounce --active
acumbamail webhooks smtp-config --url https://... --no-active  # disable

acumbamail webhooks list-get --list-id 123
acumbamail webhooks list-config --list-id 123 --url https://myapp.com/hooks/list \
  --subscribes --unsubscribes --active
```

---

## Python SDK — Methods Without CLI

These methods exist in the Python client but have no CLI command:

### Templates

```python
# List templates (includes auto-generated campaign templates with available=False)
templates = client.get_templates()
# → [Template(id=123, name="Welcome", content="..."), ...]
# Quirk: the API does not return content in the listing — Template.content = "" unless just created

# Filter only available ones
available = [t for t in client.get_templates() if t.id]

# Create template
tmpl = client.create_template(
    template_name="mi-plantilla",
    html_content="<h1>Hola *|FNAME|*</h1><a href='*|UNSUBSCRIBE_URL|*'>Baja</a>",
    subject="Asunto por defecto",
)
# → Template(id=9493654, name="mi-plantilla", content="...")

# Duplicate template
copia = client.duplicate_template(
    template_name="mi-plantilla-copia",
    origin_template_id=9493654,
)
# → Template(id=9493655, name="mi-plantilla-copia", content="")
# Quirk: content="" in the returned object (not retrieved from the server)

# get_templates_by_name() does NOT work — the server always returns 404
```

### Subscribers — Advanced Methods

```python
# Full details of a subscriber
details = client.get_subscriber_details(list_id=1138335, subscriber_email="user@x.com")
# → SubscriberDetails(id=123, email="user@x.com", status="active", create_date=..., fields={...})
# Quirk: list_id is None in the object (not included in the API response)

# Inactive subscribers (unsubscribes, bounces) in a date range
from datetime import datetime
inactive = client.get_inactive_subscribers(
    list_id=1138335,
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
)
# → [InactiveSubscriber(email="user@x.com", reason=3, reason_date=...)]

# With full_info=False (faster): returns emails only
emails = client.get_inactive_subscribers(
    list_id=1138335,
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
    full_info=False,
)
# → ["user1@x.com", "user2@x.com", ...]

# Custom fields of a list
fields = client.get_fields(list_id=1138335)
# → {"email": "email", "nombre": "char", "-curso >opcion1,opcion2": "combobox"}
# Quirk: combobox format = "-field_name >opt1,opt2,opt3"

# Fields with their TAGs (for merge tags in HTML)
merge_fields = client.get_merge_fields(list_id=1138335)
# → {"EMAIL": "email", "NOMBRE": "char", "CURSO": "combobox"}
# Returns {TAG: type} — different from get_fields which returns {name: type}

# Add a custom field to a list
client.add_merge_tag(list_id=1138335, field_name="telefono", field_type="char")

# List forms
forms = client.get_forms(list_id=1138335)
# → {} if no forms are configured

# Delete all subscribers from a list (destructive!)
client.delete_all_subscribers(list_id=1138335)
```

### Campaign Analytics

```python
campaign_id = 3294239

# Clicks
clicks = client.get_campaign_clicks(campaign_id)
# → [CampaignClick(url="...", clicks=45, unique_clicks=38, click_rate=0.09, ...)]
# → [] if no clicks

# Opens (with per-subscriber detail)
openers = client.get_campaign_openers(campaign_id)
# → [CampaignOpener(email="...", opened_at=datetime, ip="...", browser="...", os="...")]
# → [] if no opens

# Tracked links
links = client.get_campaign_links(campaign_id)
# → [] if no data

# Soft bounces
bounces = client.get_campaign_soft_bounces(campaign_id)
# → [CampaignSoftBounce(email="...", bounced_at=..., reason="...")]
# → [] if no data

# By browser/OS (return [] if no data — not {})
by_browser = client.get_campaign_openers_by_browser(campaign_id)
by_os = client.get_campaign_openers_by_os(campaign_id)

# By country (returns {} if no data — different from the above which return [])
by_country = client.get_campaign_openers_by_countries(campaign_id)
# → {} empty, or {"ES": 120, "MX": 45, ...}

# By ISP (always includes Gmail/Hotmail/Yahoo/Others even if 0)
by_isp = client.get_campaign_information_by_isp(campaign_id)
# → {"Gmail": {"opened": 45, "unopened": 120, ...}, "Hotmail": {...}, "Yahoo": {...}, "Others": {...}}

# Stats by date range (for a LIST, not a campaign)
from datetime import datetime
stats = client.get_stats_by_date(
    list_id=1138335,
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
)
# → {"total_sent": 5000, "opened": 1200, "unique_clicks": 450, "hard_bounces": 30, ...}
# NOTE: takes list_id (not campaign_id) and returns totals for the period (not per date)
```

### Send With Template

```python
# Send a campaign using an existing template
campaign = client.send_template_campaign(
    name="Newsletter con template",
    subject="Asunto del email",
    template_id=9493654,
    list_ids=[1138335],
    from_email="sender@domain.com",  # optional if default is set
    from_name="Mi Empresa",           # optional if default is set
)
```

### SMTP

```python
# Available SMTP credits
credits = client.get_smtp_credits()
# → 499923 (int)
# Quirk: the API returns {"Creditos": int} with capital C — the SDK normalizes it

# The following require an activated SMTP plan (return 401 without it):
# client.send_single_email(to_email, subject, content, ...)
# client.send_emails(...)
# client.send_certified_email(...)
# client.get_email_status(email_id)
```

---

## Non-Functional Methods (Server Bugs)

| Method | Error | Status |
|--------|-------|--------|
| `get_list_segments(list_id)` | 404 — endpoint does not exist on the server | Unusable |
| `get_list_subs_stats(list_id)` | Timeout — server does not respond | Unusable |
| `get_templates_by_name(name)` | 404 — documented but not implemented | Unusable (emits UserWarning) |
| `batch_delete_subscribers(...)` | 500 — server bug | Implemented, but fails |

---

## Output Format & jq

```bash
# IDs of all lists
acumbamail lists list | jq '[.[].id]'

# Find list by name
acumbamail lists list | jq '.[] | select(.name == "Newsletter")'

# See campaign IDs only (list only returns id+name)
acumbamail campaigns list | jq '[.[].id]'

# Open rate
acumbamail campaigns stats --campaign-id 999 | \
  jq '.opened / .total_delivered * 100 | round | tostring + "%"'

# Active subscribers in a list
acumbamail subscribers list --list-id 123 | jq '[.[] | select(.is_active == true)]'
```

## Common Workflows

### Import Subscribers From CSV

```bash
python3 -c "
import csv, json, sys
rows = list(csv.DictReader(sys.stdin))
print(json.dumps(rows))
" < subs.csv > subs.json

acumbamail subscribers batch-add --list-id 123 --file subs.json --update
```

### Full Newsletter (Create + Send + View Stats)

```bash
# 1. Create and send
acumbamail campaigns create \
  --name "Newsletter $(date +%Y-%m-%d)" \
  --subject "Novedades de esta semana" \
  --html-file newsletter.html \
  --list-id 1138335 \
  --from-email sender@domain.com \
  | jq '{id: .id, name: .name}'

# 2. View stats 24h later
acumbamail campaigns stats --campaign-id CAMPAIGN_ID | \
  jq '{open_rate: (.opened / .total_delivered * 100 | round | tostring + "%"),
       click_rate: (.unique_clicks / .total_delivered * 100 | round | tostring + "%")}'
```

### Install Skills

```bash
acumbamail install-skills      # locally
acumbamail install-skills -g   # globally (~/.claude/skills/)
```

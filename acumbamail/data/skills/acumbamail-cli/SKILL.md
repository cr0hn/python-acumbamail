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
# ⚠️ Solo activos. `lists list` reporta subscribers_count con bajas+bounces incluidos —
# comparar ambos numeros directamente lleva a creer que faltan suscriptores.
acumbamail subscribers list --status inactive     # bajas+bounces de TODA LA CUENTA
# ⚠️ --status inactive NO admite --list-id y falla si se lo pasas: getInactiveSubscribers
# es global de cuenta y los inactivos vienen con list_id nulo, asi que filtrar por lista
# es imposible. No existe --status all: sumaria una lista con la cuenta entera.
# --date-from/--date-to (YYYY-MM-DD) acotan el rango; por defecto 2000-01-01 → hoy.
# Para saber el estado de emails concretos DE UNA LISTA (incluidos los "not verified",
# que no salen en ningun listado): acumbamail subscribers check --list-id 123 --email x@y.com

acumbamail subscribers add --list-id 123 --email user@example.com
acumbamail subscribers add --list-id 123 --email user@example.com --fields '{"nombre": "Juan"}'
# → {"email": "user@example.com", "list_id": 123}

acumbamail subscribers delete --list-id 123 --email user@example.com
# → {"deleted": true, "email": "user@example.com", "list_id": 123}

acumbamail subscribers search --query user@example.com
# → [{"email": "user@example.com", "status": "active", "list_id": 123, "id": 456}, ...]
# ⚠️ NO devuelve "not verified" (doble opt-in sin confirmar), ni por email exacto. Usa `check`.

acumbamail subscribers unsubscribe --list-id 123 --email user@example.com
# → {"unsubscribed": true, "email": "user@example.com", "list_id": 123}

# Bulk import from JSON: [{"email": "a@x.com"}, {"email": "b@x.com", "nombre": "Bob"}]
acumbamail subscribers batch-add --list-id 123 --file subs.json
acumbamail subscribers batch-add --list-id 123 --file subs.json --update  # update if already exists
# → [{"email": "a@x.com", "subscriber_id": 111}, ...]

# Comprueba el estado REAL de emails concretos (uno a uno, via getSubscriberDetails) —
# la unica via que ve "not verified". Ni list, ni search, ni get_inactive_subscribers,
# ni los exports CSV los muestran (verificado 2026-08-03 contra la API real).
acumbamail subscribers check --list-id 123 --email a@x.com --email b@x.com
acumbamail subscribers check --list-id 123 --file emails.json   # JSON: ["a@x.com", "b@x.com"]
# → [{"email": "a@x.com", "found": true, "status": "not verified", "id": 456, "fields": {...}}, ...]
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
- **No segment targeting**: `createCampaign` only accepts `lists` (list IDs). There is NO `segment_id` parameter — confirmed against official API docs. Acumbamail segments exist in the UI only, not in the API.

### `webhooks` — Webhooks

```bash
acumbamail webhooks smtp-get
acumbamail webhooks smtp-config --url https://myapp.com/hooks/smtp --delivered --hard-bounce --active
acumbamail webhooks smtp-config --url https://... --no-active  # disable

acumbamail webhooks list-get --list-id 123
acumbamail webhooks list-config --list-id 123 --url https://myapp.com/hooks/list \
  --subscribes --unsubscribes --active
```

### `automations` — Automation Workflows

Automations use **browser session auth** (not the API token). Run `acumbamail automations login` once — session saved to `~/.config/acumbamail/session.json`, lasts 30 days.

```bash
# One-time login (opens Chrome — log in visually, CLI captures session)
acumbamail automations login

# List all automations
acumbamail automations list
# → [{"id": 41497, "name": "bienvenida-newsletter", "active": true, ...}]

# Deploy from YAML (creates if new, replaces steps if name matches — idempotent)
acumbamail automations deploy workflow.yaml
# → {"workflow_id": 41497, "action": "created", "active": false}
# ⚠️ ALWAYS deploys as active: false — must activate separately (see quirks)

# Export existing automation to YAML (even ones built in the GUI)
acumbamail automations export --name "bienvenida-newsletter" > workflow.yaml
acumbamail automations export --id 41497 > workflow.yaml

# Delete
acumbamail automations delete --name "bienvenida-newsletter"
acumbamail automations delete --id 41497
```

**YAML schema:**

```yaml
name: bienvenida-newsletter          # unique identifier — used for idempotent deploy
description: "Optional description"

trigger:
  list_id: 1406220                   # Acumbamail list ID
  event: subscriber_added            # subscriber_added | specific_date | segment_added
  apply_to_existing: false

steps:
  - type: email_template
    subject: "¡Bienvenido!"
    template_id: 9563943             # must exist — create via SDK client.create_template()
    from_email: sender@domain.com    # must be a verified sender
    from_name: "Mi Empresa"
    track_urls: true
    track_analytics: true

  - type: delay
    wait: 3
    unit: days                       # minutes | hours | days

  - type: condition
    on_match:
      - type: email_template
        subject: "Oferta"
        template_id: 456
    on_no_match:
      - type: delay
        wait: 1
        unit: days

  - type: webhook
    url: https://hooks.example.com/notify
    method: POST                     # GET | POST | PUT | PATCH | DELETE

  - type: update_field
    field: curso
    value: curso_a

  - type: move_to
    list_id: 1138336
```

**Activate after deploy (CLI deploys as inactive):**

```python
import json
from acumbamail.automation_client import AutomationClient

with open('/Users/cr0hn/.config/acumbamail/session.json') as f:
    s = json.load(f)

client = AutomationClient.from_session(s['sessionid'], s['csrftoken'])
client.activate_workflow(41497)   # or deactivate_workflow(id)
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
# Full details of a subscriber -- the ONLY way to see "not verified" (unconfirmed
# double opt-in) subscribers. get_subscribers/search_subscriber/get_inactive_subscribers
# and the CSV exports never show them (verified 2026-08-03 against the real API).
details = client.get_subscriber_details(list_id=1138335, subscriber_email="user@x.com")
# → SubscriberDetails(id=123, email="user@x.com", status="active", create_date=..., fields={...})
# Quirk: list_id is None in the object (not included in the API response)

# Inactive subscribers (unsubscribes, bounces) in a date range
# ⚠️ GLOBAL DE CUENTA, no per-list, and the API doesn't say so: it silently accepted
# a list_id parameter in earlier SDK versions, returned HTTP 200, and IGNORED it --
# verified with a nonexistent list_id, which still returned the account's full total.
# The SDK now REJECTS list_id explicitly (AcumbamailValidationError) instead of lying
# about filtering. There is no server-side way to scope this to one list; cross-reference
# against get_subscribers(list_id) or get_subscriber_details(list_id, email) instead.
from datetime import datetime
inactive = client.get_inactive_subscribers(
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
    full_info=True,
)
# → [InactiveSubscriber(email="user@x.com", reason=3, reason_date=..., reason_label=InactiveReason.UNSUBSCRIBED)]
# reason codes (undocumented by Acumbamail, verified 2026-08-03 by cross-referencing
# 805 real inactives against CSV exports): 1 = hard bounce, 3 = voluntary unsubscribe.
# reason_label gives the readable InactiveReason enum (BOUNCE/UNSUBSCRIBED/UNKNOWN);
# the raw int stays available in `reason`.

# With full_info=False (faster): returns emails only
emails = client.get_inactive_subscribers(
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

## Known Quirks & Gotchas

### Automations deploy always creates inactive
`acumbamail automations deploy` always returns `"active": false` regardless of previous state. Activate via the Python SDK `AutomationClient.from_session()` (see automations section above).

### Multi-account: API token ≠ automation session
Acumbamail supports multiple accounts/projects. The API token (used for lists/subscribers/campaigns) and the browser session (used for automations) can be for **different accounts**. Symptom: automation deploys successfully but doesn't appear in the web UI, or appears in a different account. Fix: run `acumbamail automations login` while logged into the correct account in Chrome, then redeploy.

### `batch-add` CLI bug
`acumbamail subscribers batch-add` may fail with `int() argument must be a string... not 'dict'` when the API returns an unexpected response shape. Workaround: add subscribers one by one with `subscribers add` in a loop:
```bash
for email in a@x.com b@x.com; do
  acumbamail subscribers add --list-id 123 --email "$email"
done
```

### Hard-bounced subscribers absent from active CSV exports
Subscribers with hard bounce status exist in the list but are excluded from "active subscribers" exports and deliveries. When comparing Moosend/other-provider exports to Acumbamail active exports, missing emails may be hard bounces — not truly absent. Verify with `subscribers add` (returns "already exists" if present).

### `get_inactive_subscribers` is global to the account, not per-list (verified 2026-08-03)
The `list_id` parameter looked like a filter but wasn't: the API accepted it, returned HTTP 200, and silently ignored it. Proof: `list_id=99999999` (a list that doesn't exist) still returned the account's full 805 inactive subscribers, same as no filter at all. The SDK now rejects `list_id` outright with `AcumbamailValidationError` — it never worked, so failing loudly beats failing silently. There is no server-side way to scope this endpoint to one list; cross-reference the returned emails against `get_subscribers(list_id)` or `get_subscriber_details(list_id, email)` per candidate instead.

### `reason` codes in `get_inactive_subscribers(full_info=True)` were documented backwards
`acumbamail-openapi.yaml` used to say reason 3 was a hard bounce. Verified 2026-08-03 by cross-referencing 805 real inactive subscribers against the account's CSV exports: **reason=1 is the hard bounce** (6 cases, none in any export — that's exactly the gap between `subscribers_count` and the CSV totals) and **reason=3 is the voluntary unsubscribe** (799 cases, 795 of them literally present in the unsubscribes CSV). Fixed in the OpenAPI spec and exposed as a readable `InactiveReason` enum (`reason_label` field) on `InactiveSubscriber`, alongside the raw `reason` int.

### "not verified" subscribers are invisible everywhere except `get_subscriber_details`
A subscriber mid doble-opt-in (never confirmed) does not show up in `get_subscribers`, `search_subscriber`, `get_inactive_subscribers`, or any CSV export — verified against a real case (`wieckcl@yahoo.es` in list 1415406, `status='not verified'` since 2026-07-05, invisible everywhere except a targeted lookup). There is no way to *enumerate* them; the API only reveals the status when you ask about one exact email via `get_subscriber_details(list_id, email)`. The CLI wraps this as `subscribers check --email ... [--email ...] | --file emails.json`, which is the tool to run before concluding "this email isn't in the list" — "doesn't appear" is not the same as "doesn't exist".

### `email_template` step requires existing template
Cannot deploy an automation with `type: email_template` without a valid `template_id`. Create the template first via Python SDK `client.create_template(...)`, capture the returned `id`, then reference it in the YAML.

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

### Deploy Welcome Automation (full flow)

```bash
# 1. Create the email template via Python SDK
python3 -c "
from acumbamail import AcumbamailClient
client = AcumbamailClient(auth_token='TOKEN', default_sender_email='sender@domain.com')
tmpl = client.create_template(
    template_name='bienvenida',
    html_content=open('welcome.html').read(),
    subject='Asunto por defecto',
)
print(tmpl.id)
"
# → 9563943

# 2. Write YAML referencing that template_id
# (see automations YAML schema above)

# 3. Login to automations (once per 30 days)
acumbamail automations login

# 4. Deploy (creates inactive)
acumbamail automations deploy bienvenida.yaml
# → {"workflow_id": 41497, "action": "created", "active": false}

# 5. Activate via SDK
python3 -c "
import json
from acumbamail.automation_client import AutomationClient
s = json.load(open('/Users/cr0hn/.config/acumbamail/session.json'))
AutomationClient.from_session(s['sessionid'], s['csrftoken']).activate_workflow(41497)
"
```

### Install Skills

```bash
acumbamail install-skills      # locally
acumbamail install-skills -g   # globally (~/.claude/skills/)
```

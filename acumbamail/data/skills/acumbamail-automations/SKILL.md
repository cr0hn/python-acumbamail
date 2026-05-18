---
name: acumbamail-automations
description: Use when working with Acumbamail automation workflows via the CLI or SDK — deploying from YAML, exporting existing automations, listing/deleting workflows, or calling the internal automation API directly. Contains the full reverse-engineered API reference.
---

# Acumbamail Automations

Manage Acumbamail email automation workflows as code. Define sequences of emails, delays, conditions, and webhooks in YAML, then deploy them with one command.

## Authentication

Automation commands require a **browser-based login** (NOT the API token). The automation API uses Django session auth and Acumbamail's login page blocks programmatic requests via bot detection.

**First-time setup (and every ~30 days when session expires):**
```bash
acumbamail automations login
# → Opens Chrome, you log in visually
# → Session saved to ~/.config/acumbamail/session.json (valid 30 days)
```

After login, all other commands work without credentials:
```bash
acumbamail automations list
acumbamail automations deploy workflow.yaml
```

> **Why no email/password flag?** Acumbamail blocks programmatic login via httpx (bot detection on the login page). The CLI uses Playwright with a dedicated Chrome profile (`~/.config/acumbamail/chrome_profile/`) to open a real browser for login.

> **Session lifetime**: 30 days. CSRF tokens are NOT needed to keep the session alive — they're only required for write operations. The session expires based on `SESSION_COOKIE_AGE` set by Acumbamail.

## CLI Commands

```bash
# Login (required first time and every ~30 days)
acumbamail automations login

# List all automations
acumbamail automations list

# Deploy automation from YAML (idempotent — creates or updates by name)
acumbamail automations deploy workflow.yaml

# Export an existing automation to YAML
acumbamail automations export --id 36215
acumbamail automations export --name "email-bienvenida"

# Delete an automation
acumbamail automations delete --id 36215
acumbamail automations delete --name "email-bienvenida"
```

## YAML Schema

### Minimal example

```yaml
name: bienvenida
trigger:
  list_id: 1138335
  event: subscriber_added
steps:
  - type: email_template
    subject: "¡Bienvenido!"
    template_id: 8986619
    # Note: from_email/from_name use account defaults unless you have a verified sender
```

### Full schema reference

```yaml
name: <string>                    # required, used for idempotent deploy
description: <string>             # optional

trigger:
  list_id: <int>                  # Acumbamail list ID
  event: subscriber_added         # subscriber_added | specific_date | segment_added
  apply_to_existing: false        # bool, default false

steps:
  # --- Send email using a template ---
  - type: email_template
    name: <string>                # optional custom name
    subject: <string>             # required
    preheader: <string>           # optional preview text
    from_email: <string>          # optional — MUST be a verified sender in Acumbamail
                                  # If omitted or not verified, account default is used
    from_name: <string>           # optional — same caveat as from_email
    template_id: <int>            # required — Acumbamail template ID
    track_urls: true              # optional, default true
    track_analytics: true         # optional, default true

  # --- Send plain text email ---
  - type: plain_email
    subject: <string>
    from_email: <string>
    from_name: <string>
    content: <string>             # HTML or plain text

  # --- Wait ---
  - type: delay
    wait: <int>                   # amount
    unit: minutes | hours | days  # default: days

  # --- Conditional split (creates Fork + two Condition nodes) ---
  - type: condition
    on_match:                     # steps if condition is true
      - type: ...
    on_no_match:                  # steps if condition is false
      - type: ...

  # --- Wait until condition is met ---
  - type: until
    steps:                        # steps inside the until loop
      - type: delay
        wait: 1
        unit: days

  # --- HTTP webhook ---
  - type: webhook
    url: <string>                 # required
    method: POST                  # GET | POST | PUT | PATCH | DELETE

  # --- Update subscriber custom field ---
  - type: update_field
    field: <string>               # field name
    value: <string>               # new value

  # --- Move subscriber to another list ---
  - type: move_to
    list_id: <int>

  # --- Send SMS (requires SMS plan) ---
  - type: sms
    message: <string>
```

### Trigger events

| YAML value | Meaning |
|------------|---------|
| `subscriber_added` | New subscriber joins the list |
| `specific_date` | Triggered on a specific date |
| `segment_added` | Subscriber enters a segment |

---

## Internal API Reference

> This section documents the reverse-engineered API. Use it when calling the API directly (e.g. in scripts or SDK extensions).

### Base URL

```
https://acumbamail.com/automation/api/
```

### Authentication (internal API)

The automation API uses Django session authentication. The public API token does **not** work.

**Login form quirks (discovered via reverse engineering):**
- Form POSTs to `/login/2fa/` (not `/login/`)
- Field names are `auth-username` and `auth-password` (not `username`/`password`)
- Requires hidden field `login_view-current_step: auth`
- **Programmatic login via httpx/requests does NOT work** — Acumbamail's login page returns 403 to non-browser HTTP clients. Use `acumbamail automations login` (Playwright) instead.

**After login, include in all requests:**
- Cookie: `sessionid=<value>; csrftoken=<value>; backend=py3`
- Write requests additionally need: `X-CSRFToken: <csrftoken>`, `Origin: https://acumbamail.com`, `Referer: https://acumbamail.com/automation/workflow-list`

**Session lifetime:** 30 days (`SESSION_COOKIE_AGE`). CSRF is NOT needed to keep the session alive — only for write operation validation. Session only expires if you log out or 30 days pass.

### Workflow endpoints

```
GET    /automation/api/basic-workflow/           → [{id, name, description, active, booting}]
GET    /automation/api/basic-workflow/{id}/      → {id, name, description, active, booting}
GET    /automation/api/workflow/{id}/            → full workflow with node tree
POST   /automation/api/workflow/                 → create {name, description?} → 201
PATCH  /automation/api/basic-workflow/{id}/      → update {name?, description?, active?} → 200
DELETE /automation/api/workflow/{id}/            → 204
```

### Node endpoints

Pattern: `{nodeType}` = lowercase node type string (e.g. `trigger`, `delay`, `sendtemplate`)

```
POST   /automation/api/{nodeType}/         → create node → 201
PUT    /automation/api/{nodeType}/{id}/    → update node → 200
DELETE /automation/api/{nodeType}/{id}/    → delete node → 204
```

**Create node body:**
```json
{
  "sourceId": "<parentNodeId>",
  "nodeType": "Delay",
  "workflow": "36215",
  "siblings": []
}
```

> **Critical quirk:** `sourceId` alone does NOT establish the parent-child link. After creating a node, you MUST also PUT the parent node with the new child in its `siblings` array:
> ```
> PUT /automation/api/trigger/235966/
> Body: {...trigger_data, "siblings": ["275542"]}
> ```

> **SendTemplate quirk:** The `template` (template ID) field is **required at CREATE time**, not just at update. Include it in the POST body.

> **from_email quirk:** The `from_email` field in SendTemplate PUT is strictly validated against Acumbamail's verified sender list. If the email is not registered as a verified sender, the PUT returns 400. Omit `from_email` in the PUT to use the account default.

### Node types reference

| UI label | `nodeType` value | Key fields |
|----------|-----------------|------------|
| Empezar | `Trigger` | `workflow_list`, `trigger_reason.reason_index` (0=new subscriber, 1=specific date, 2=segment), `trigger_reason.config.apply_to_subscribers_in_list` |
| Esperar | `Delay` | `wait_time` (int), `wait_unit` (0=minutes, 2=days), `send_in_monday`…`send_in_sunday` (bool) |
| Hasta | `Until` | `type_of_decision`, `decision.config` |
| Plantilla | `SendTemplate` | `subject`, `preheader`, `from_email`, `from_name`, `template` (int ID), `tracking_urls`, `tracking_analytics` |
| Email texto | `SendPlainEmail` | `subject`, `from_email`, `from_name`, `content` |
| Bifurcación | `Fork` | parent node of two `Condition` siblings |
| Condición | `Condition` | `evaluation` (true=match branch, false=no-match branch), `type_of_decision`, `decision.config` |
| Webhook | `Webhook` | `url`, `method` |
| Cuando | `When` | `type_of_decision`, `decision.config` |
| Actualizar campo | `UpdateField` | field name + value in `decision.config` |
| Mover a | `MoveTo` | target list ID in `decision.config` |
| SMS | `SendSms` | `message` |

### Workflow JSON structure

The full workflow (`GET /automation/api/workflow/{id}/`) returns a recursive tree via `siblings`:

```json
{
  "id": "36215",
  "name": "mi-automatizacion",
  "description": null,
  "active": false,
  "booting": false,
  "entry_point": {
    "id": "235966",
    "nodeType": "Trigger",
    "workflow": 36215,
    "workflow_list": 1138335,
    "trigger_reason": {
      "reason_index": 0,
      "config": {"apply_to_subscribers_in_list": false}
    },
    "siblings": [
      {
        "id": "239953",
        "nodeType": "Delay",
        "wait_time": 1,
        "wait_unit": 2,
        "siblings": [
          {
            "id": "234069",
            "nodeType": "SendTemplate",
            "subject": "¡Bienvenido!",
            "preheader": "...",
            "from_email": "dani@example.com",
            "from_name": "Dani",
            "template": 8986619,
            "siblings": []
          }
        ]
      }
    ]
  }
}
```

### Trigger reason indexes

| `reason_index` | Event |
|---------------|-------|
| 0 | New subscriber in list |
| 1 | Specific date |
| 2 | New subscriber in segment |

### Delay wait_unit values

| `wait_unit` | Unit |
|-------------|------|
| 0 | Minutes |
| 2 | Days |

---

## Deploy algorithm (idempotent by name)

When `acumbamail automations deploy workflow.yaml` runs:

1. Load session from `~/.config/acumbamail/session.json`
2. `GET /basic-workflow/` → find workflow matching `name`
3. **Not found** → `POST /workflow/` → build node tree:
   - Update Trigger settings via PUT
   - For each step: `POST /automation/api/{nodeType}/` then `PUT` with settings
   - After each node creation: `PUT` the parent to add the new node to its `siblings` array
   - For `email_template`: include `template` ID in the POST create body
   - For `condition`: create `Fork` → two `Condition` children, each with their own sub-tree
4. **Found** → delete all nodes except Trigger → rebuild tree from scratch
5. Output: `{"workflow_id": 36215, "action": "created|updated", "active": false}`

**Node linking sequence (3 calls per linear node):**
```
POST /automation/api/delay/          → 201 {id: "new_delay_id", ...}
PUT  /automation/api/delay/{id}/     → 200 (update wait_time, wait_unit, etc.)
PUT  /automation/api/trigger/{id}/   → 200 (add new_delay_id to trigger.siblings)
```

---

## Examples

### Deploy a welcome sequence

```bash
# First, login (opens Chrome for you to log in)
acumbamail automations login

# Create the YAML
cat > welcome.yaml << 'EOF'
name: bienvenida-newsletter
trigger:
  list_id: 1138335
  event: subscriber_added
steps:
  - type: email_template
    subject: "¡Bienvenido a la newsletter!"
    template_id: 123456
    # from_email uses account default (must be a verified sender if specified)
  - type: delay
    wait: 3
    unit: days
  - type: email_template
    subject: "¿Cómo te va?"
    template_id: 123457
EOF

acumbamail automations deploy welcome.yaml
```

### List all automations and filter active ones

```bash
acumbamail automations list | jq '[.[] | select(.active == true)]'
```

### Export and re-deploy to another account

```bash
acumbamail automations export --name "bienvenida-newsletter" > backup.yaml
# Edit backup.yaml, change list_id, etc.
ACUMBAMAIL_EMAIL=other@account.com acumbamail automations deploy backup.yaml
```

### Check automation IDs for use in API calls

```bash
acumbamail automations list | jq '.[].id'
```

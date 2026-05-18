---
name: acumbamail-automations
description: Use when working with Acumbamail automation workflows via the CLI or SDK — deploying from YAML, exporting existing automations, listing/deleting workflows, or calling the internal automation API directly. Contains the full reverse-engineered API reference.
---

# Acumbamail Automations

Manage Acumbamail email automation workflows as code. Define sequences of emails, delays, conditions, and webhooks in YAML, then deploy them with one command.

## Authentication

Automation commands use **web session auth** (NOT the API token). Set:

```bash
export ACUMBAMAIL_EMAIL=user@example.com
export ACUMBAMAIL_PASSWORD=your_password
```

Or pass `--email`/`--password` per command.

> The public `ACUMBAMAIL_TOKEN` does **not** work for automations. The automation API is a separate internal API at `https://acumbamail.com/automation/api/` that requires a Django session.

## CLI Commands

```bash
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
    from_email: hello@example.com
    from_name: Mi empresa
    template_id: 8986619
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
    from_email: <string>          # required
    from_name: <string>           # required
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

**Login flow:**
1. `GET /login/` → parse `<input name="csrfmiddlewaretoken">` from HTML response
2. `POST /login/` with form body:
   ```
   username=user@example.com&password=secret&csrfmiddlewaretoken=<csrf>
   Content-Type: application/x-www-form-urlencoded
   ```
3. Session cookie (`sessionid`) is set in the response — include it in all subsequent requests
4. Re-extract CSRF from any automation page for write operations, add as `X-CSRFToken` header

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
  "workflow": 36215,
  "siblings": []
}
```

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

1. Login with email + password → get session
2. `GET /basic-workflow/` → find workflow matching `name`
3. **Not found** → `POST /workflow/` → build node tree sequentially:
   - Start with Trigger node (the entry point)
   - For each step in YAML: `POST /automation/api/{nodeType}/` with `sourceId` = previous node's ID
   - For `condition` type: create `Fork` node first, then two `Condition` children
4. **Found** → `GET /workflow/{id}/` → diff existing tree vs desired YAML → apply changes
5. Output: `{"workflow_id": 36215, "action": "created|updated", "active": false}`

---

## Examples

### Deploy a welcome sequence

```bash
cat > welcome.yaml << 'EOF'
name: bienvenida-newsletter
trigger:
  list_id: 1138335
  event: subscriber_added
steps:
  - type: email_template
    subject: "¡Bienvenido a la newsletter!"
    from_email: hola@example.com
    from_name: Mi Empresa
    template_id: 123456
  - type: delay
    wait: 3
    unit: days
  - type: email_template
    subject: "¿Cómo te va?"
    from_email: hola@example.com
    from_name: Mi Empresa
    template_id: 123457
EOF

export ACUMBAMAIL_EMAIL=user@example.com
export ACUMBAMAIL_PASSWORD=secret
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

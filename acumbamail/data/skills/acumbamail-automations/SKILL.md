---
name: acumbamail-automations
description: Use when working with the `acumbamail automations` CLI commands — logging in, deploying workflows from YAML, exporting existing automations, or listing/deleting them. Covers authentication, YAML schema, and known quirks.
---

# Acumbamail Automations CLI

Manage Acumbamail email automation workflows as code via the `acumbamail automations` command group.

## First-time setup: Login

Automations require a browser-based login (separate from the API token):

```bash
acumbamail automations login
```

This opens Chrome. Log in to Acumbamail visually, wait for the dashboard to load, and the CLI captures your session automatically. The session is saved to `~/.config/acumbamail/session.json` and lasts **30 days**.

> Repeat `acumbamail automations login` every 30 days or whenever commands return auth errors.

## Commands

```bash
# Login (opens Chrome)
acumbamail automations login

# List all automations
acumbamail automations list

# Deploy from YAML (creates if not exists, updates if name matches)
acumbamail automations deploy workflow.yaml

# Export an existing automation to YAML
acumbamail automations export --name "email-bienvenida"
acumbamail automations export --id 36215

# Delete
acumbamail automations delete --name "email-bienvenida"
acumbamail automations delete --id 36215
```

All output is JSON (except `export`, which outputs YAML). Errors go to stderr + exit 1.

## YAML Schema

```yaml
name: bienvenida-newsletter          # required — used as unique identifier for idempotent deploy
description: "Optional description"  # optional

trigger:
  list_id: 1138335                   # required — Acumbamail list ID
  event: subscriber_added            # subscriber_added | specific_date | segment_added
  apply_to_existing: false           # bool, default false

steps:
  # Send an email using a saved template
  - type: email_template
    subject: "¡Bienvenido!"
    preheader: "Preview text"        # optional
    template_id: 8986619             # required — template ID from Acumbamail
    from_email: hello@domain.com     # optional — must be a verified sender in Acumbamail
    from_name: "Mi Empresa"          # optional
    track_urls: true                 # optional, default true
    track_analytics: true            # optional, default true

  # Wait N time units
  - type: delay
    wait: 3
    unit: days                       # minutes | hours | days

  # Conditional branch
  - type: condition
    on_match:                        # steps when condition is true
      - type: email_template
        subject: "Oferta especial"
        template_id: 456
    on_no_match:                     # steps when condition is false
      - type: delay
        wait: 1
        unit: days

  # Wait until a condition is met, then continue
  - type: until
    steps:
      - type: delay
        wait: 1
        unit: days

  # HTTP webhook
  - type: webhook
    url: https://hooks.example.com/notify
    method: POST                     # GET | POST | PUT | PATCH | DELETE

  # Update a subscriber's custom field
  - type: update_field
    field: curso
    value: curso_a

  # Move subscriber to another list
  - type: move_to
    list_id: 1138336
```

### Trigger events

| `event` | When it fires |
|---------|--------------|
| `subscriber_added` | When a subscriber joins the list |
| `specific_date` | On a specific date |
| `segment_added` | When a subscriber enters a segment |

## Known quirks

**`from_email` must be a verified sender.** If you specify `from_email` in an `email_template` step and that email is not registered as a verified sender in your Acumbamail account, the deploy will fail. Omit `from_email` to use your account's default sender.

**Deploy is idempotent by `name`.** If a workflow with the same name already exists, `deploy` replaces its steps entirely (deletes and rebuilds). The name is the only key — rename the YAML `name` field to deploy a new workflow alongside the existing one.

**`email_template` requires `template_id`.** You cannot deploy an email step without specifying an existing Acumbamail template ID. Get IDs with `acumbamail templates list`.

## Examples

### Welcome email sequence

```yaml
name: bienvenida
trigger:
  list_id: 1138335
  event: subscriber_added
steps:
  - type: email_template
    subject: "¡Bienvenido!"
    template_id: 8986619
  - type: delay
    wait: 3
    unit: days
  - type: email_template
    subject: "¿Cómo te va?"
    template_id: 8986620
```

```bash
acumbamail automations login
acumbamail automations deploy bienvenida.yaml
# → {"workflow_id": 36215, "action": "created", "active": false}
```

### Export, edit, redeploy

```bash
acumbamail automations export --name "bienvenida" > bienvenida.yaml
# edit bienvenida.yaml
acumbamail automations deploy bienvenida.yaml
# → {"workflow_id": 36215, "action": "updated", "active": false}
```

### Filter active automations

```bash
acumbamail automations list | jq '[.[] | select(.active == true)]'
```

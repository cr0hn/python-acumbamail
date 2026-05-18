# Automations Feature — Design Spec

**Date:** 2026-05-18  
**Status:** Approved

---

## Context

Acumbamail supports visual workflow automations (email sequences, conditionals, delays, webhooks). They are created via a web UI at `https://acumbamail.com/automation/`. The goal is to manage these automations as code: define them in YAML, deploy them via CLI, export existing ones, list and delete them.

---

## Key Constraint (Reverse-Engineered)

The automation API lives at `https://acumbamail.com/automation/api/` and uses **Django session auth** (cookies + CSRF token). The public API token (`ACUMBAMAIL_TOKEN`) does **not** work here. This drives the entire architecture.

---

## Architecture

### New files

```
acumbamail/
├── automation_client.py        # AutomationClient — session-based HTTP client
├── automation_models.py        # Automation, AutomationNode dataclasses
├── automation_yaml.py          # YAML parser + tree compiler
└── cli/commands/
    └── automations.py          # list, deploy, export, delete commands

acumbamail/data/skills/
└── acumbamail-automations/
    └── SKILL.md                # Claude Code skill with full API docs

tests/
├── test_automation_client.py
├── test_automation_yaml.py
└── test_automation_cli.py
```

### `AutomationClient` (acumbamail/automation_client.py)

Separate from `AcumbamailClient`. Uses `httpx.Client` with a persistent cookie jar.

```python
class AutomationClient:
    BASE_URL = "https://acumbamail.com"

    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self._client = httpx.Client()
        self._logged_in = False

    def login(self) -> None:
        # GET /login/ → extract CSRF from input[name=csrfmiddlewaretoken]
        # POST /login/ with credentials + CSRF → session cookie stored in client

    # Workflow CRUD
    def list_workflows(self) -> list[Automation]
    def get_workflow(self, workflow_id: int) -> Automation
    def create_workflow(self, name: str, description: str | None) -> Automation
    def update_workflow(self, workflow_id: int, *, name: str | None, active: bool | None) -> Automation
    def delete_workflow(self, workflow_id: int) -> None
    def activate_workflow(self, workflow_id: int) -> Automation
    def deactivate_workflow(self, workflow_id: int) -> Automation

    # Node CRUD
    def create_node(self, node_type: str, workflow_id: int, source_id: str, siblings: list) -> dict
    def update_node(self, node_type: str, node_id: str, payload: dict) -> dict
    def delete_node(self, node_type: str, node_id: str) -> None
```

Auth is env vars `ACUMBAMAIL_EMAIL` + `ACUMBAMAIL_PASSWORD` or `--email`/`--password` CLI flags.

### `automation_models.py`

```python
@dataclass
class Automation:
    id: int
    name: str
    description: str | None
    active: bool
    booting: bool
    entry_point: AutomationNode | None = None  # only in full detail

@dataclass
class AutomationNode:
    id: str
    node_type: str          # Trigger, Delay, SendTemplate, etc.
    workflow_id: int
    parent_id: int
    siblings: list[AutomationNode]
    # type-specific fields stored in extra: dict
    extra: dict
```

### `automation_yaml.py`

Two functions:
- `load_yaml(path) -> dict` — parse + validate YAML
- `compile_yaml(data: dict, client: AutomationClient) -> None` — deploy tree

Compile algorithm (idempotent by name):
1. `list_workflows()` → find by name
2. If not found → `create_workflow(name, description)` → deploy full tree
3. If found → `get_workflow(id)` → diff existing tree vs desired → apply minimal changes

---

## API Reference (Reverse-Engineered)

### Auth

- Session cookie (`sessionid`) + CSRF token required
- Login: `GET /login/` → extract CSRF from `<input name="csrfmiddlewaretoken">` → `POST /login/` with `username=<email>&password=<pwd>&csrfmiddlewaretoken=<csrf>`
- All write requests need `X-CSRFToken: <csrf>` header

### Workflow Endpoints

| Method | URL | Body | Success |
|--------|-----|------|---------|
| GET | `/automation/api/basic-workflow/` | — | 200, `[{id, name, description, active, booting}]` |
| GET | `/automation/api/workflow/{id}/` | — | 200, full tree |
| GET | `/automation/api/basic-workflow/{id}/` | — | 200, basic info |
| POST | `/automation/api/workflow/` | `{name, description?}` | 201, full workflow |
| PATCH | `/automation/api/basic-workflow/{id}/` | `{name?, description?, active?}` | 200, basic info |
| DELETE | `/automation/api/workflow/{id}/` | — | 204 |

### Node Endpoints

Pattern: `{nodeType}` is the lowercase node type (e.g. `trigger`, `delay`, `sendtemplate`).

| Method | URL | Body | Success |
|--------|-----|------|---------|
| POST | `/automation/api/{nodeType}/` | `{sourceId, nodeType, workflow, siblings}` | 201 |
| PUT | `/automation/api/{nodeType}/{id}/` | full node object | 200 |
| DELETE | `/automation/api/{nodeType}/{id}/` | — | 204 |

### Node Types

| UI Name | API nodeType | Key fields |
|---------|-------------|------------|
| Empezar | `trigger` | `workflow_list`, `trigger_reason.reason_index` (0=new subscriber, 1=specific date, 2=new segment member), `trigger_reason.config` |
| Esperar | `delay` | `wait_time`, `wait_unit` (0=minutes, 1=hours [unconfirmed], 2=days), `send_in_monday`…`send_in_sunday` |
| Hasta | `until` | `type_of_decision`, `decision.config` |
| Plantilla | `sendtemplate` | `subject`, `preheader`, `from_email`, `from_name`, `template` (ID), `tracking_urls`, `tracking_analytics` |
| Email texto | `sendplainemail` | `subject`, `from_email`, `from_name`, `content` |
| Condición | `condition` | `evaluation` (true/false branch), `decision.config` |
| Bifurcación | `fork` | parent of two `condition` siblings |
| Webhook | `webhook` | `url`, `method` |
| Cuando | `when` | `type_of_decision`, `decision.config` |
| Actualizar campo | `updatefield` | `field_name`, `field_value` |
| Mover a | `moveto` | `target_list_id` |
| SMS | `sendsms` | `message` |

### Workflow JSON structure (tree via `siblings`)

```json
{
  "id": "36215",
  "name": "prueba",
  "active": false,
  "entry_point": {
    "nodeType": "Trigger",
    "workflow_list": 1138335,
    "trigger_reason": {"reason_index": 0, "config": {"apply_to_subscribers_in_list": false}},
    "siblings": [
      {
        "nodeType": "Until",
        "siblings": [
          {
            "nodeType": "Delay",
            "wait_time": 1,
            "wait_unit": 2,
            "siblings": [
              {
                "nodeType": "SendTemplate",
                "subject": "Asunto",
                "template": 8986619,
                "siblings": []
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

## YAML Schema

```yaml
name: email-bienvenida
description: "Opcional"          # null if omitted

trigger:
  list_id: 1138335
  event: subscriber_added         # subscriber_added | specific_date | segment_added
  apply_to_existing: false

steps:
  - type: email_template
    name: paso-bienvenida         # optional, auto-generated if absent
    subject: "¡Bienvenido!"
    preheader: "Lo que vas a leer..."
    from_email: dani@example.com
    from_name: Dani
    template_id: 8986619
    track_urls: true
    track_analytics: true

  - type: delay
    wait: 3
    unit: days                    # minutes | hours | days

  - type: condition
    on_match:
      - type: email_template
        subject: "Oferta"
        template_id: 456
    on_no_match:
      - type: delay
        wait: 1
        unit: days

  - type: until
    steps:
      - type: delay
        wait: 1
        unit: days

  - type: webhook
    url: https://hooks.example.com/notify
    method: POST

  - type: update_field
    field: curso
    value: curso_a

  - type: move_to
    list_id: 1138336
```

---

## CLI Commands

```bash
# Auth env vars (used by all automation commands)
export ACUMBAMAIL_EMAIL=user@example.com
export ACUMBAMAIL_PASSWORD=secret

# List all automations
acumbamail automations list

# Deploy from YAML (create or update idempotently)
acumbamail automations deploy workflow.yaml

# Export existing automation to YAML
acumbamail automations export --id 36215 > workflow.yaml
acumbamail automations export --name "email-bienvenida" > workflow.yaml

# Delete
acumbamail automations delete --id 36215
acumbamail automations delete --name "email-bienvenida"
```

---

## Deploy Algorithm (idempotent by name)

```
1. login()
2. existing = list_workflows()
3. match = find existing by name
4. if match is None:
     wf = create_workflow(name, description)
     build_tree(wf.id, entry_point=None, steps=yaml.steps)
   else:
     wf = get_workflow(match.id)
     diff_and_patch(wf, yaml)
5. output JSON: {workflow_id, action: created|updated, active}
```

For `build_tree`: POST nodes sequentially, threading each node's ID as `sourceId` for the next. For `condition` type: POST a `Fork` node, then POST two `Condition` children (one with `evaluation: true`, one with `evaluation: false`), each with their own sub-steps.

For the diff in the update path (MVP): delete all existing nodes except the Trigger, then rebuild the tree from scratch.

---

## Testing

- Unit tests: mock `httpx` (same pattern as existing `pytest-httpx` tests)
- No contract tests for automations (API requires web session, not API token)
- Test YAML parsing separately from client calls

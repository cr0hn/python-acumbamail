# Automations Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `acumbamail automations` CLI commands (list, deploy, export, delete) that manage Acumbamail workflow automations as YAML code.

**Architecture:** Separate `AutomationClient` using Django session auth (email+password, not API token) + `AutomationNode`/`Automation` models + YAML compiler that translates a declarative YAML schema into sequential API calls to build the node tree.

**Tech Stack:** Python 3.13, httpx, PyYAML, Typer, pytest-httpx

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `acumbamail/automation_models.py` | Create | `Automation` + `AutomationNode` dataclasses |
| `acumbamail/automation_client.py` | Create | Session-based HTTP client for `automation/api/` |
| `acumbamail/automation_yaml.py` | Create | YAML load/validate/compile/export |
| `acumbamail/cli/commands/automations.py` | Create | Typer commands: list, deploy, export, delete |
| `acumbamail/cli/utils.py` | Modify | Add `get_automation_client()` helper |
| `acumbamail/cli/main.py` | Modify | Register `automations` group |
| `acumbamail/__init__.py` | Modify | Export `AutomationClient`, `Automation`, `AutomationNode` |
| `pyproject.toml` | Modify | Move `pyyaml` from dev to main dependencies |
| `tests/test_automation_models.py` | Create | Model parsing tests |
| `tests/test_automation_client.py` | Create | HTTP client tests (pytest-httpx) |
| `tests/test_automation_yaml.py` | Create | YAML parse + compile + export tests |
| `tests/test_automation_cli.py` | Create | CLI tests (CliRunner + mock) |
| `CHANGELOG.md` | Modify | Document new feature |

---

## Task 1: Automation models

**Files:**
- Create: `acumbamail/automation_models.py`
- Create: `tests/test_automation_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_automation_models.py
import pytest
from acumbamail.automation_models import Automation, AutomationNode


class TestAutomationNode:
    def test_from_api_basic_fields(self):
        data = {
            "id": "234068",
            "parent_id": 0,
            "workflow": 35925,
            "nodeType": "Trigger",
            "siblings": [],
            "workflow_list": 1140700,
            "trigger_reason": {"reason_index": 0, "config": {"apply_to_subscribers_in_list": False}},
        }
        node = AutomationNode.from_api(data)
        assert node.id == "234068"
        assert node.node_type == "Trigger"
        assert node.workflow_id == 35925
        assert node.parent_id == 0
        assert node.siblings == []
        assert node.extra["workflow_list"] == 1140700

    def test_from_api_recursive_siblings(self):
        data = {
            "id": "100",
            "parent_id": 0,
            "workflow": 1,
            "nodeType": "Trigger",
            "siblings": [
                {
                    "id": "101",
                    "parent_id": 100,
                    "workflow": 1,
                    "nodeType": "Delay",
                    "wait_time": 1,
                    "wait_unit": 2,
                    "siblings": [],
                }
            ],
        }
        node = AutomationNode.from_api(data)
        assert len(node.siblings) == 1
        assert node.siblings[0].id == "101"
        assert node.siblings[0].node_type == "Delay"
        assert node.siblings[0].extra["wait_time"] == 1


class TestAutomation:
    def test_from_basic_api(self):
        data = {"id": 35925, "name": "test", "description": None, "active": True, "booting": False}
        automation = Automation.from_basic_api(data)
        assert automation.id == 35925
        assert automation.name == "test"
        assert automation.active is True
        assert automation.entry_point is None

    def test_from_full_api_with_entry_point(self):
        data = {
            "id": "35925",
            "name": "test",
            "description": None,
            "active": True,
            "booting": False,
            "entry_point": {
                "id": "234068",
                "parent_id": 0,
                "workflow": 35925,
                "nodeType": "Trigger",
                "siblings": [],
            },
        }
        automation = Automation.from_full_api(data)
        assert automation.id == 35925
        assert automation.entry_point is not None
        assert automation.entry_point.node_type == "Trigger"

    def test_from_full_api_id_as_string(self):
        data = {"id": "36215", "name": "prueba", "description": None, "active": False, "booting": False, "entry_point": None}
        automation = Automation.from_full_api(data)
        assert automation.id == 36215
        assert isinstance(automation.id, int)
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
cd /Users/cr0hn/Dropbox/Projects/py-acumbamail
uv run pytest tests/test_automation_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'acumbamail.automation_models'`

- [ ] **Step 3: Create `acumbamail/automation_models.py`**

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class AutomationNode:
    id: str
    node_type: str
    workflow_id: int
    parent_id: int
    siblings: list[AutomationNode]
    extra: dict

    @classmethod
    def from_api(cls, data: dict) -> AutomationNode:
        siblings = [cls.from_api(s) for s in data.get("siblings", [])]
        skip = {"id", "nodeType", "workflow", "parent_id", "siblings"}
        extra = {k: v for k, v in data.items() if k not in skip}
        return cls(
            id=str(data["id"]),
            node_type=data["nodeType"],
            workflow_id=int(data["workflow"]),
            parent_id=int(data.get("parent_id", 0)),
            siblings=siblings,
            extra=extra,
        )


@dataclass
class Automation:
    id: int
    name: str
    description: Optional[str]
    active: bool
    booting: bool
    entry_point: Optional[AutomationNode] = None

    @classmethod
    def from_basic_api(cls, data: dict) -> Automation:
        return cls(
            id=int(data["id"]),
            name=data["name"],
            description=data.get("description"),
            active=data["active"],
            booting=data["booting"],
        )

    @classmethod
    def from_full_api(cls, data: dict) -> Automation:
        entry_point = None
        if data.get("entry_point"):
            entry_point = AutomationNode.from_api(data["entry_point"])
        return cls(
            id=int(data["id"]),
            name=data["name"],
            description=data.get("description"),
            active=data["active"],
            booting=data["booting"],
            entry_point=entry_point,
        )
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
uv run pytest tests/test_automation_models.py -v
```
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add acumbamail/automation_models.py tests/test_automation_models.py
git commit -m "feat(automations): add Automation + AutomationNode models"
```

---

## Task 2: AutomationClient — login + core HTTP

**Files:**
- Create: `acumbamail/automation_client.py`
- Create: `tests/test_automation_client.py` (login section)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_automation_client.py
import pytest
from pytest_httpx import HTTPXMock
from acumbamail.automation_client import AutomationClient

BASE = "https://acumbamail.com"
LOGIN_HTML = '<form><input name="csrfmiddlewaretoken" value="csrf_token_123"></form>'


@pytest.fixture
def client():
    return AutomationClient("user@test.com", "password123")


def mock_login(httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/login/", text=LOGIN_HTML, status_code=200)
    httpx_mock.add_response(method="POST", url=f"{BASE}/login/", text="<html>ok</html>", status_code=200)


class TestLogin:
    def test_login_extracts_and_stores_csrf(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        client.login()
        assert client._csrf_token == "csrf_token_123"

    def test_login_sends_credentials_in_post(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        client.login()
        requests = httpx_mock.get_requests()
        post_req = requests[1]
        assert post_req.method == "POST"
        body = post_req.content.decode()
        assert "user%40test.com" in body or "user@test.com" in body
        assert "password123" in body

    def test_extract_csrf_from_html(self, client):
        html = '<input name="csrfmiddlewaretoken" value="abc123">'
        assert client._extract_csrf(html) == "abc123"

    def test_extract_csrf_raises_if_missing(self, client):
        with pytest.raises(ValueError, match="CSRF token not found"):
            client._extract_csrf("<html>no token here</html>")
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_client.py::TestLogin -v
```
Expected: `ModuleNotFoundError: No module named 'acumbamail.automation_client'`

- [ ] **Step 3: Create `acumbamail/automation_client.py`**

```python
from __future__ import annotations
import re
from typing import Optional
import httpx
from .automation_models import Automation, AutomationNode

BASE_URL = "https://acumbamail.com"


class AutomationClient:
    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self._client = httpx.Client(follow_redirects=True)
        self._csrf_token: Optional[str] = None

    def _extract_csrf(self, html: str) -> str:
        match = re.search(
            r'name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']+)["\']', html
        ) or re.search(
            r'value=["\']([^"\']+)["\'][^>]*name=["\']csrfmiddlewaretoken["\']', html
        )
        if not match:
            raise ValueError("CSRF token not found in page")
        return match.group(1)

    def login(self) -> None:
        resp = self._client.get(f"{BASE_URL}/login/")
        resp.raise_for_status()
        self._csrf_token = self._extract_csrf(resp.text)
        resp = self._client.post(
            f"{BASE_URL}/login/",
            data={
                "username": self._email,
                "password": self._password,
                "csrfmiddlewaretoken": self._csrf_token,
            },
            headers={"Referer": f"{BASE_URL}/login/"},
        )
        if resp.text:
            try:
                self._csrf_token = self._extract_csrf(resp.text)
            except ValueError:
                pass

    def _headers(self) -> dict:
        return {"X-CSRFToken": self._csrf_token or "", "Content-Type": "application/json"}

    def _get(self, path: str) -> httpx.Response:
        resp = self._client.get(f"{BASE_URL}{path}")
        resp.raise_for_status()
        return resp

    def _post(self, path: str, json: dict) -> httpx.Response:
        resp = self._client.post(f"{BASE_URL}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp

    def _patch(self, path: str, json: dict) -> httpx.Response:
        resp = self._client.patch(f"{BASE_URL}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp

    def _put(self, path: str, json: dict) -> httpx.Response:
        resp = self._client.put(f"{BASE_URL}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp

    def _delete(self, path: str) -> None:
        resp = self._client.delete(f"{BASE_URL}{path}", headers=self._headers())
        resp.raise_for_status()
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
uv run pytest tests/test_automation_client.py::TestLogin -v
```
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add acumbamail/automation_client.py tests/test_automation_client.py
git commit -m "feat(automations): add AutomationClient with login + core HTTP"
```

---

## Task 3: AutomationClient — workflow CRUD

**Files:**
- Modify: `acumbamail/automation_client.py`
- Modify: `tests/test_automation_client.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_automation_client.py`:

```python
WORKFLOW_BASIC = {"id": 35925, "name": "test", "description": None, "active": True, "booting": False}
WORKFLOW_FULL = {
    "id": "35925", "name": "test", "description": None,
    "active": True, "booting": False,
    "entry_point": {"id": "234068", "parent_id": 0, "workflow": 35925, "nodeType": "Trigger", "siblings": []},
}


class TestListWorkflows:
    def test_returns_list_of_automations(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(
            url=f"{BASE}/automation/api/basic-workflow/",
            json=[WORKFLOW_BASIC],
        )
        client.login()
        result = client.list_workflows()
        assert len(result) == 1
        assert result[0].id == 35925
        assert result[0].name == "test"

    def test_returns_empty_list(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(url=f"{BASE}/automation/api/basic-workflow/", json=[])
        client.login()
        assert client.list_workflows() == []


class TestGetWorkflow:
    def test_returns_automation_with_entry_point(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(url=f"{BASE}/automation/api/workflow/35925/", json=WORKFLOW_FULL)
        client.login()
        result = client.get_workflow(35925)
        assert result.id == 35925
        assert result.entry_point is not None
        assert result.entry_point.node_type == "Trigger"


class TestCreateWorkflow:
    def test_posts_name_and_description(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/automation/api/workflow/",
            json=WORKFLOW_FULL,
            status_code=201,
        )
        client.login()
        result = client.create_workflow("test", "desc")
        post_req = httpx_mock.get_requests()[-1]
        body = _json.loads(post_req.content)
        assert body["name"] == "test"
        assert body["description"] == "desc"
        assert result.id == 35925

    def test_description_can_be_none(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{BASE}/automation/api/workflow/", json=WORKFLOW_FULL, status_code=201)
        client.login()
        client.create_workflow("test")
        post_req = httpx_mock.get_requests()[-1]
        body = _json.loads(post_req.content)
        assert body["description"] is None


class TestDeleteWorkflow:
    def test_sends_delete_request(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(method="DELETE", url=f"{BASE}/automation/api/workflow/35925/", status_code=204)
        client.login()
        client.delete_workflow(35925)
        delete_req = httpx_mock.get_requests()[-1]
        assert delete_req.method == "DELETE"


class TestActivateWorkflow:
    def test_activate_sends_patch_with_active_true(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="PATCH",
            url=f"{BASE}/automation/api/basic-workflow/35925/",
            json={**WORKFLOW_BASIC, "active": True},
        )
        client.login()
        result = client.activate_workflow(35925)
        patch_req = httpx_mock.get_requests()[-1]
        body = _json.loads(patch_req.content)
        assert body["active"] is True
        assert result.active is True

    def test_deactivate_sends_patch_with_active_false(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="PATCH",
            url=f"{BASE}/automation/api/basic-workflow/35925/",
            json={**WORKFLOW_BASIC, "active": False},
        )
        client.login()
        client.deactivate_workflow(35925)
        patch_req = httpx_mock.get_requests()[-1]
        body = _json.loads(patch_req.content)
        assert body["active"] is False
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_client.py -v -k "Workflow"
```
Expected: `AttributeError: 'AutomationClient' object has no attribute 'list_workflows'`

- [ ] **Step 3: Add workflow CRUD methods to `acumbamail/automation_client.py`**

Append to the `AutomationClient` class (after `_delete`):

```python
    def list_workflows(self) -> list[Automation]:
        return [Automation.from_basic_api(item) for item in self._get("/automation/api/basic-workflow/").json()]

    def get_workflow(self, workflow_id: int) -> Automation:
        return Automation.from_full_api(self._get(f"/automation/api/workflow/{workflow_id}/").json())

    def create_workflow(self, name: str, description: Optional[str] = None) -> Automation:
        return Automation.from_full_api(
            self._post("/automation/api/workflow/", {"name": name, "description": description}).json()
        )

    def update_workflow(self, workflow_id: int, *, name: Optional[str] = None, active: Optional[bool] = None) -> Automation:
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if active is not None:
            payload["active"] = active
        return Automation.from_basic_api(
            self._patch(f"/automation/api/basic-workflow/{workflow_id}/", payload).json()
        )

    def delete_workflow(self, workflow_id: int) -> None:
        self._delete(f"/automation/api/workflow/{workflow_id}/")

    def activate_workflow(self, workflow_id: int) -> Automation:
        return self.update_workflow(workflow_id, active=True)

    def deactivate_workflow(self, workflow_id: int) -> Automation:
        return self.update_workflow(workflow_id, active=False)
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
uv run pytest tests/test_automation_client.py -v
```
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add acumbamail/automation_client.py tests/test_automation_client.py
git commit -m "feat(automations): add workflow CRUD methods to AutomationClient"
```

---

## Task 4: AutomationClient — node CRUD

**Files:**
- Modify: `acumbamail/automation_client.py`
- Modify: `tests/test_automation_client.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_automation_client.py`:

```python
NODE_DELAY_RESPONSE = {
    "id": "275481", "parent_id": 0, "workflow": 36215,
    "nodeType": "Delay", "wait_time": 1, "wait_unit": 2, "siblings": [],
}


class TestNodeCRUD:
    def test_create_node_posts_correct_payload(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/automation/api/delay/",
            json=NODE_DELAY_RESPONSE,
            status_code=201,
        )
        client.login()
        result = client.create_node("Delay", 36215, "235966")
        post_req = httpx_mock.get_requests()[-1]
        body = _json.loads(post_req.content)
        assert body["sourceId"] == "235966"
        assert body["nodeType"] == "Delay"
        assert body["workflow"] == "36215"
        assert result["id"] == "275481"

    def test_create_node_uses_lowercase_nodetype_in_url(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/automation/api/sendtemplate/",
            json={"id": "999", "nodeType": "SendTemplate", "workflow": 1, "siblings": []},
            status_code=201,
        )
        client.login()
        client.create_node("SendTemplate", 1, "100")
        post_req = httpx_mock.get_requests()[-1]
        assert "/automation/api/sendtemplate/" in str(post_req.url)

    def test_update_node_sends_put(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="PUT",
            url=f"{BASE}/automation/api/delay/275481/",
            json={**NODE_DELAY_RESPONSE, "wait_time": 3},
        )
        client.login()
        result = client.update_node("Delay", "275481", {**NODE_DELAY_RESPONSE, "wait_time": 3})
        put_req = httpx_mock.get_requests()[-1]
        body = _json.loads(put_req.content)
        assert body["wait_time"] == 3
        assert result["wait_time"] == 3

    def test_delete_node_sends_delete(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="DELETE",
            url=f"{BASE}/automation/api/delay/275481/",
            status_code=204,
        )
        client.login()
        client.delete_node("Delay", "275481")
        delete_req = httpx_mock.get_requests()[-1]
        assert delete_req.method == "DELETE"
        assert "/automation/api/delay/275481/" in str(delete_req.url)
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_client.py::TestNodeCRUD -v
```
Expected: `AttributeError: 'AutomationClient' object has no attribute 'create_node'`

- [ ] **Step 3: Add node CRUD methods to `acumbamail/automation_client.py`**

Append to `AutomationClient` class:

```python
    def create_node(self, node_type: str, workflow_id: int, source_id: str, siblings: Optional[list] = None) -> dict:
        return self._post(f"/automation/api/{node_type.lower()}/", {
            "sourceId": source_id,
            "nodeType": node_type,
            "workflow": str(workflow_id),
            "siblings": siblings or [],
        }).json()

    def update_node(self, node_type: str, node_id: str, payload: dict) -> dict:
        return self._put(f"/automation/api/{node_type.lower()}/{node_id}/", payload).json()

    def delete_node(self, node_type: str, node_id: str) -> None:
        self._delete(f"/automation/api/{node_type.lower()}/{node_id}/")
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
uv run pytest tests/test_automation_client.py -v
```
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add acumbamail/automation_client.py tests/test_automation_client.py
git commit -m "feat(automations): add node CRUD methods to AutomationClient"
```

---

## Task 5: YAML load and validation

**Files:**
- Create: `acumbamail/automation_yaml.py`
- Create: `tests/test_automation_yaml.py`
- Modify: `pyproject.toml` (move pyyaml to main deps)

- [ ] **Step 1: Move pyyaml to main dependencies in `pyproject.toml`**

Change lines 11-14 from:
```toml
dependencies = [
    "httpx>=0.28.1,<0.29.0",
    "typer>=0.15.0",
]
```
to:
```toml
dependencies = [
    "httpx>=0.28.1,<0.29.0",
    "pyyaml>=6.0.1",
    "typer>=0.15.0",
]
```

And remove `"pyyaml>=6.0.3",` from the `[dependency-groups] dev` section.

Run: `uv sync`

- [ ] **Step 2: Write failing tests**

```python
# tests/test_automation_yaml.py
import pytest
import yaml
from pathlib import Path
from acumbamail.automation_yaml import load_yaml, validate_yaml


class TestLoadYaml:
    def test_load_valid_yaml(self, tmp_path):
        p = tmp_path / "wf.yaml"
        p.write_text("""
name: test-automation
trigger:
  list_id: 1138335
  event: subscriber_added
steps:
  - type: delay
    wait: 1
    unit: days
""")
        data = load_yaml(str(p))
        assert data["name"] == "test-automation"
        assert data["trigger"]["list_id"] == 1138335
        assert data["steps"][0]["type"] == "delay"

    def test_load_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_yaml("/nonexistent/path/file.yaml")


class TestValidateYaml:
    def test_raises_if_name_missing(self):
        with pytest.raises(ValueError, match="name"):
            validate_yaml({"trigger": {"list_id": 1}})

    def test_raises_if_list_id_missing(self):
        with pytest.raises(ValueError, match="list_id"):
            validate_yaml({"name": "test", "trigger": {}})

    def test_raises_on_invalid_event(self):
        with pytest.raises(ValueError, match="event"):
            validate_yaml({"name": "test", "trigger": {"list_id": 1, "event": "invalid_event"}})

    def test_valid_minimal_yaml_passes(self):
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335}})

    def test_valid_yaml_with_event_passes(self):
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335, "event": "subscriber_added"}})
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335, "event": "specific_date"}})
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335, "event": "segment_added"}})
```

- [ ] **Step 3: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_yaml.py -v
```
Expected: `ModuleNotFoundError: No module named 'acumbamail.automation_yaml'`

- [ ] **Step 4: Create `acumbamail/automation_yaml.py`**

```python
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import yaml

if TYPE_CHECKING:
    from .automation_client import AutomationClient
    from .automation_models import Automation, AutomationNode

_TRIGGER_EVENT_MAP = {
    "subscriber_added": 0,
    "specific_date": 1,
    "segment_added": 2,
}

_WAIT_UNIT_MAP = {
    "minutes": 0,
    "hours": 1,
    "days": 2,
}


def load_yaml(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    validate_yaml(data)
    return data


def validate_yaml(data: dict) -> None:
    if not data.get("name"):
        raise ValueError("YAML missing required field: name")
    trigger = data.get("trigger") or {}
    if not trigger.get("list_id"):
        raise ValueError("YAML missing required field: trigger.list_id")
    event = trigger.get("event")
    if event and event not in _TRIGGER_EVENT_MAP:
        raise ValueError(f"Invalid trigger.event: {event!r}. Valid values: {list(_TRIGGER_EVENT_MAP)}")
```

- [ ] **Step 5: Run tests — confirm pass**

```bash
uv run pytest tests/test_automation_yaml.py::TestLoadYaml tests/test_automation_yaml.py::TestValidateYaml -v
```
Expected: `7 passed`

- [ ] **Step 6: Commit**

```bash
git add acumbamail/automation_yaml.py tests/test_automation_yaml.py pyproject.toml uv.lock
git commit -m "feat(automations): add YAML load/validate + move pyyaml to main deps"
```

---

## Task 6: YAML compiler — create path (trigger + linear steps)

**Files:**
- Modify: `acumbamail/automation_yaml.py`
- Modify: `tests/test_automation_yaml.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_automation_yaml.py`:

```python
from unittest.mock import MagicMock, call
from acumbamail.automation_yaml import deploy_yaml, _build_tree, _deploy_step
from acumbamail.automation_models import Automation, AutomationNode


def make_trigger_node(node_id="234068"):
    return AutomationNode(
        id=node_id, node_type="Trigger", workflow_id=35925,
        parent_id=0, siblings=[], extra={"workflow_list": 1138335},
    )

def make_automation(wf_id=35925, name="test", trigger_id="234068"):
    return Automation(
        id=wf_id, name=name, description=None, active=False, booting=False,
        entry_point=make_trigger_node(trigger_id),
    )


class TestDeployStep:
    def test_delay_creates_and_updates_node(self):
        client = MagicMock()
        client.create_node.return_value = {
            "id": "111", "nodeType": "Delay", "workflow": 1, "siblings": [],
            "wait_time": 1, "wait_unit": 2,
        }
        step = {"type": "delay", "wait": 3, "unit": "days"}
        node_id = _deploy_step(35925, "234068", step, client)
        client.create_node.assert_called_once_with("Delay", 35925, "234068")
        client.update_node.assert_called_once()
        update_args = client.update_node.call_args[0]
        assert update_args[0] == "delay"
        assert update_args[1] == "111"
        assert update_args[2]["wait_time"] == 3
        assert update_args[2]["wait_unit"] == 2
        assert node_id == "111"

    def test_delay_unit_minutes(self):
        client = MagicMock()
        client.create_node.return_value = {"id": "111", "nodeType": "Delay", "workflow": 1, "siblings": []}
        _deploy_step(1, "100", {"type": "delay", "wait": 5, "unit": "minutes"}, client)
        update_args = client.update_node.call_args[0][2]
        assert update_args["wait_unit"] == 0

    def test_email_template_creates_and_updates(self):
        client = MagicMock()
        client.create_node.return_value = {
            "id": "222", "nodeType": "SendTemplate", "workflow": 1, "siblings": [],
        }
        step = {
            "type": "email_template",
            "subject": "Hello!",
            "from_email": "a@b.com",
            "from_name": "A",
            "template_id": 9999,
        }
        node_id = _deploy_step(1, "100", step, client)
        update_args = client.update_node.call_args[0][2]
        assert update_args["subject"] == "Hello!"
        assert update_args["template"] == 9999
        assert update_args["from_email"] == "a@b.com"
        assert node_id == "222"

    def test_webhook_creates_and_updates(self):
        client = MagicMock()
        client.create_node.return_value = {"id": "333", "nodeType": "Webhook", "workflow": 1, "siblings": []}
        node_id = _deploy_step(1, "100", {"type": "webhook", "url": "https://x.com/hook", "method": "POST"}, client)
        update_args = client.update_node.call_args[0][2]
        assert update_args["url"] == "https://x.com/hook"
        assert node_id == "333"

    def test_unknown_type_raises(self):
        client = MagicMock()
        with pytest.raises(ValueError, match="Unknown step type"):
            _deploy_step(1, "100", {"type": "unknown_type"}, client)


class TestDeployYaml:
    def test_creates_new_workflow_when_not_found(self):
        client = MagicMock()
        client.list_workflows.return_value = []
        client.create_workflow.return_value = make_automation()
        client.create_node.return_value = {
            "id": "500", "nodeType": "Delay", "workflow": 35925, "siblings": [],
        }
        data = {
            "name": "test",
            "trigger": {"list_id": 1138335, "event": "subscriber_added"},
            "steps": [{"type": "delay", "wait": 1, "unit": "days"}],
        }
        result = deploy_yaml(data, client)
        client.create_workflow.assert_called_once_with("test", None)
        assert result["action"] == "created"
        assert result["workflow_id"] == 35925

    def test_returns_updated_when_workflow_exists(self):
        client = MagicMock()
        existing = make_automation()
        client.list_workflows.return_value = [existing]
        client.get_workflow.return_value = make_automation()
        data = {
            "name": "test",
            "trigger": {"list_id": 1138335},
            "steps": [],
        }
        result = deploy_yaml(data, client)
        client.create_workflow.assert_not_called()
        assert result["action"] == "updated"
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_yaml.py::TestDeployStep tests/test_automation_yaml.py::TestDeployYaml -v
```
Expected: `ImportError` or `AttributeError` (functions not yet defined)

- [ ] **Step 3: Add compiler functions to `acumbamail/automation_yaml.py`**

Append to `automation_yaml.py`:

```python
def deploy_yaml(data: dict, client: "AutomationClient") -> dict:
    name = data["name"]
    description = data.get("description")
    existing = next((w for w in client.list_workflows() if w.name == name), None)

    if existing is None:
        workflow = client.create_workflow(name, description)
        trigger_id = workflow.entry_point.id
        _update_trigger(workflow.entry_point, data.get("trigger", {}), client)
        _build_tree(workflow.id, trigger_id, data.get("steps", []), client)
        return {"workflow_id": workflow.id, "action": "created", "active": workflow.active}
    else:
        full = client.get_workflow(existing.id)
        _delete_all_nodes_except_trigger(full, client)
        _update_trigger(full.entry_point, data.get("trigger", {}), client)
        _build_tree(existing.id, full.entry_point.id, data.get("steps", []), client)
        return {"workflow_id": existing.id, "action": "updated", "active": existing.active}


def _update_trigger(trigger_node: "AutomationNode", trigger_data: dict, client: "AutomationClient") -> None:
    reason_index = _TRIGGER_EVENT_MAP.get(trigger_data.get("event", "subscriber_added"), 0)
    payload = {
        **trigger_node.extra,
        "id": trigger_node.id,
        "nodeType": "Trigger",
        "workflow": trigger_node.workflow_id,
        "siblings": [s.id for s in trigger_node.siblings],
        "workflow_list": trigger_data.get("list_id", trigger_node.extra.get("workflow_list")),
        "trigger_reason": {
            "reason_index": reason_index,
            "config": {"apply_to_subscribers_in_list": trigger_data.get("apply_to_existing", False)},
        },
    }
    client.update_node("trigger", trigger_node.id, payload)


def _delete_all_nodes_except_trigger(workflow: "Automation", client: "AutomationClient") -> None:
    def _delete_subtree(node: "AutomationNode") -> None:
        for child in node.siblings:
            _delete_subtree(child)
        if node.node_type != "Trigger":
            client.delete_node(node.node_type, node.id)
    if workflow.entry_point:
        _delete_subtree(workflow.entry_point)


def _build_tree(workflow_id: int, source_id: str, steps: list, client: "AutomationClient") -> str:
    last_id = source_id
    for step in steps:
        last_id = _deploy_step(workflow_id, last_id, step, client)
    return last_id


def _deploy_step(workflow_id: int, source_id: str, step: dict, client: "AutomationClient") -> str:
    stype = step["type"]

    if stype == "delay":
        node = client.create_node("Delay", workflow_id, source_id)
        client.update_node("delay", node["id"], {
            **node,
            "wait_time": step.get("wait", 1),
            "wait_unit": _WAIT_UNIT_MAP.get(step.get("unit", "days"), 2),
        })
        return node["id"]

    elif stype == "email_template":
        node = client.create_node("SendTemplate", workflow_id, source_id)
        client.update_node("sendtemplate", node["id"], {
            **node,
            "name": step.get("name", f"step-{node['id']}"),
            "subject": step["subject"],
            "preheader": step.get("preheader", ""),
            "from_email": step["from_email"],
            "from_name": step["from_name"],
            "template": step["template_id"],
            "tracking_urls": step.get("track_urls", True),
            "tracking_analytics": step.get("track_analytics", True),
        })
        return node["id"]

    elif stype == "plain_email":
        node = client.create_node("SendPlainEmail", workflow_id, source_id)
        client.update_node("sendplainemail", node["id"], {
            **node,
            "subject": step["subject"],
            "from_email": step["from_email"],
            "from_name": step["from_name"],
            "content": step["content"],
        })
        return node["id"]

    elif stype == "webhook":
        node = client.create_node("Webhook", workflow_id, source_id)
        client.update_node("webhook", node["id"], {
            **node,
            "url": step["url"],
            "method": step.get("method", "POST"),
        })
        return node["id"]

    elif stype == "update_field":
        node = client.create_node("UpdateField", workflow_id, source_id)
        client.update_node("updatefield", node["id"], {**node, "field_name": step["field"], "field_value": step["value"]})
        return node["id"]

    elif stype == "move_to":
        node = client.create_node("MoveTo", workflow_id, source_id)
        client.update_node("moveto", node["id"], {**node, "target_list_id": step["list_id"]})
        return node["id"]

    elif stype == "condition":
        fork = client.create_node("Fork", workflow_id, source_id)
        cond_true = client.create_node("Condition", workflow_id, fork["id"])
        client.update_node("condition", cond_true["id"], {**cond_true, "evaluation": True})
        _build_tree(workflow_id, cond_true["id"], step.get("on_match", []), client)
        cond_false = client.create_node("Condition", workflow_id, fork["id"])
        client.update_node("condition", cond_false["id"], {**cond_false, "evaluation": False})
        _build_tree(workflow_id, cond_false["id"], step.get("on_no_match", []), client)
        return fork["id"]

    elif stype == "until":
        node = client.create_node("Until", workflow_id, source_id)
        _build_tree(workflow_id, node["id"], step.get("steps", []), client)
        return node["id"]

    else:
        raise ValueError(f"Unknown step type: {stype!r}")
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
uv run pytest tests/test_automation_yaml.py -v
```
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add acumbamail/automation_yaml.py tests/test_automation_yaml.py
git commit -m "feat(automations): add YAML compiler (deploy create + update paths)"
```

---

## Task 7: YAML exporter

**Files:**
- Modify: `acumbamail/automation_yaml.py`
- Modify: `tests/test_automation_yaml.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_automation_yaml.py`:

```python
from acumbamail.automation_yaml import export_yaml


def make_node(node_id, node_type, workflow_id=1, siblings=None, **extra):
    return AutomationNode(
        id=str(node_id), node_type=node_type, workflow_id=workflow_id,
        parent_id=0, siblings=siblings or [], extra=extra,
    )


class TestExportYaml:
    def test_exports_name_and_description(self):
        wf = Automation(id=1, name="test", description="my desc", active=False, booting=False,
                        entry_point=make_node(100, "Trigger", workflow_list=1138335,
                                              trigger_reason={"reason_index": 0, "config": {"apply_to_subscribers_in_list": False}}))
        result = export_yaml(wf)
        assert result["name"] == "test"
        assert result["description"] == "my desc"

    def test_exports_trigger_list_id_and_event(self):
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {"apply_to_subscribers_in_list": False}})
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        assert result["trigger"]["list_id"] == 1138335
        assert result["trigger"]["event"] == "subscriber_added"
        assert result["trigger"]["apply_to_existing"] is False

    def test_exports_delay_step(self):
        delay = make_node(200, "Delay", wait_time=3, wait_unit=2)
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {}}, siblings=[delay])
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        assert result["steps"][0]["type"] == "delay"
        assert result["steps"][0]["wait"] == 3
        assert result["steps"][0]["unit"] == "days"

    def test_exports_email_template_step(self):
        email = make_node(200, "SendTemplate", subject="Hi!", from_email="a@b.com",
                          from_name="A", template=9999, preheader="preview")
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {}}, siblings=[email])
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        step = result["steps"][0]
        assert step["type"] == "email_template"
        assert step["subject"] == "Hi!"
        assert step["template_id"] == 9999
        assert step["preheader"] == "preview"

    def test_exports_condition_as_on_match_on_no_match(self):
        cond_true = make_node(301, "Condition", evaluation=True)
        cond_false = make_node(302, "Condition", evaluation=False)
        fork = make_node(300, "Fork", siblings=[cond_true, cond_false])
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {}}, siblings=[fork])
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        step = result["steps"][0]
        assert step["type"] == "condition"
        assert "on_match" in step
        assert "on_no_match" in step
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_yaml.py::TestExportYaml -v
```
Expected: `ImportError: cannot import name 'export_yaml'`

- [ ] **Step 3: Add `export_yaml` to `acumbamail/automation_yaml.py`**

Append to `automation_yaml.py`:

```python
def export_yaml(workflow: "Automation") -> dict:
    result: dict = {"name": workflow.name}
    if workflow.description:
        result["description"] = workflow.description

    if workflow.entry_point:
        trigger = workflow.entry_point
        ev_inv = {v: k for k, v in _TRIGGER_EVENT_MAP.items()}
        reason = trigger.extra.get("trigger_reason") or {}
        result["trigger"] = {
            "list_id": trigger.extra.get("workflow_list"),
            "event": ev_inv.get(reason.get("reason_index", 0), "subscriber_added"),
            "apply_to_existing": (reason.get("config") or {}).get("apply_to_subscribers_in_list", False),
        }
        result["steps"] = _nodes_to_steps(trigger.siblings)

    return result


def _nodes_to_steps(nodes: list) -> list:
    return [s for s in (_node_to_step(n) for n in nodes) if s is not None]


def _node_to_step(node: "AutomationNode") -> Optional[dict]:
    unit_inv = {v: k for k, v in _WAIT_UNIT_MAP.items()}
    nt = node.node_type

    if nt == "Delay":
        return {"type": "delay", "wait": node.extra.get("wait_time", 1),
                "unit": unit_inv.get(node.extra.get("wait_unit", 2), "days")}
    elif nt == "SendTemplate":
        step: dict = {"type": "email_template", "subject": node.extra.get("subject", ""),
                      "from_email": node.extra.get("from_email", ""), "from_name": node.extra.get("from_name", ""),
                      "template_id": node.extra.get("template")}
        if node.extra.get("preheader"):
            step["preheader"] = node.extra["preheader"]
        return step
    elif nt == "SendPlainEmail":
        return {"type": "plain_email", "subject": node.extra.get("subject", ""),
                "from_email": node.extra.get("from_email", ""), "from_name": node.extra.get("from_name", ""),
                "content": node.extra.get("content", "")}
    elif nt == "Webhook":
        return {"type": "webhook", "url": node.extra.get("url", ""), "method": node.extra.get("method", "POST")}
    elif nt == "UpdateField":
        return {"type": "update_field", "field": node.extra.get("field_name", ""),
                "value": node.extra.get("field_value", "")}
    elif nt == "MoveTo":
        return {"type": "move_to", "list_id": node.extra.get("target_list_id")}
    elif nt == "Fork":
        on_match, on_no_match = [], []
        for child in node.siblings:
            if child.node_type == "Condition":
                if child.extra.get("evaluation"):
                    on_match = _nodes_to_steps(child.siblings)
                else:
                    on_no_match = _nodes_to_steps(child.siblings)
        return {"type": "condition", "on_match": on_match, "on_no_match": on_no_match}
    elif nt == "Until":
        return {"type": "until", "steps": _nodes_to_steps(node.siblings)}
    return None
```

- [ ] **Step 4: Run all YAML tests — confirm pass**

```bash
uv run pytest tests/test_automation_yaml.py -v
```
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add acumbamail/automation_yaml.py tests/test_automation_yaml.py
git commit -m "feat(automations): add YAML exporter (export_yaml)"
```

---

## Task 8: CLI commands + wire up

**Files:**
- Create: `acumbamail/cli/commands/automations.py`
- Modify: `acumbamail/cli/utils.py`
- Modify: `acumbamail/cli/main.py`
- Modify: `acumbamail/__init__.py`
- Create: `tests/test_automation_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_automation_cli.py
import json
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from acumbamail.automation_models import Automation

runner = CliRunner()
ENV = {"ACUMBAMAIL_EMAIL": "user@test.com", "ACUMBAMAIL_PASSWORD": "secret"}

BASIC_WF = Automation(id=35925, name="email-bienvenida", description=None, active=True, booting=False)


def make_mock_client(workflows=None):
    client = MagicMock()
    client.list_workflows.return_value = workflows or [BASIC_WF]
    return client


class TestAutomationsList:
    def test_outputs_json_list(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_fn.return_value = make_mock_client()
            result = runner.invoke(app, ["automations", "list"], env=ENV)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data[0]["id"] == 35925
        assert data[0]["name"] == "email-bienvenida"

    def test_exits_1_without_credentials(self):
        from acumbamail.cli.main import app
        result = runner.invoke(app, ["automations", "list"], env={})
        assert result.exit_code == 1


class TestAutomationsDeploy:
    def test_deploy_creates_workflow(self, tmp_path):
        from acumbamail.cli.main import app
        p = tmp_path / "wf.yaml"
        p.write_text("name: test\ntrigger:\n  list_id: 1138335\nsteps: []\n")
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            with patch("acumbamail.cli.commands.automations.deploy_yaml") as mock_deploy:
                mock_fn.return_value = MagicMock()
                mock_deploy.return_value = {"workflow_id": 999, "action": "created", "active": False}
                result = runner.invoke(app, ["automations", "deploy", str(p)], env=ENV)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["action"] == "created"

    def test_deploy_exits_1_on_missing_file(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client"):
            result = runner.invoke(app, ["automations", "deploy", "/no/such/file.yaml"], env=ENV)
        assert result.exit_code == 1


class TestAutomationsDelete:
    def test_delete_by_id(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_client = make_mock_client()
            mock_fn.return_value = mock_client
            result = runner.invoke(app, ["automations", "delete", "--id", "35925"], env=ENV)
        assert result.exit_code == 0, result.output
        mock_client.delete_workflow.assert_called_once_with(35925)

    def test_delete_by_name(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_client = make_mock_client()
            mock_fn.return_value = mock_client
            result = runner.invoke(app, ["automations", "delete", "--name", "email-bienvenida"], env=ENV)
        assert result.exit_code == 0, result.output
        mock_client.delete_workflow.assert_called_once_with(35925)

    def test_delete_exits_1_if_name_not_found(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_fn.return_value = make_mock_client()
            result = runner.invoke(app, ["automations", "delete", "--name", "nonexistent"], env=ENV)
        assert result.exit_code == 1


class TestAutomationsExport:
    def test_export_by_id_outputs_yaml(self):
        from acumbamail.cli.main import app
        from acumbamail.automation_models import AutomationNode
        trigger = AutomationNode(id="100", node_type="Trigger", workflow_id=35925,
                                 parent_id=0, siblings=[], extra={"workflow_list": 1138335,
                                 "trigger_reason": {"reason_index": 0, "config": {}}})
        full_wf = Automation(id=35925, name="email-bienvenida", description=None,
                             active=True, booting=False, entry_point=trigger)
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_client = make_mock_client()
            mock_client.get_workflow.return_value = full_wf
            mock_fn.return_value = mock_client
            result = runner.invoke(app, ["automations", "export", "--id", "35925"], env=ENV)
        assert result.exit_code == 0, result.output
        assert "email-bienvenida" in result.output
        assert "subscriber_added" in result.output
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
uv run pytest tests/test_automation_cli.py -v
```
Expected: import errors or command-not-found errors

- [ ] **Step 3: Add `get_automation_client` to `acumbamail/cli/utils.py`**

Add at the end of `acumbamail/cli/utils.py`:

```python
def get_automation_client(email: str | None, password: str | None) -> "AutomationClient":
    from acumbamail.automation_client import AutomationClient
    resolved_email = email or os.environ.get("ACUMBAMAIL_EMAIL")
    resolved_password = password or os.environ.get("ACUMBAMAIL_PASSWORD")
    if not resolved_email or not resolved_password:
        typer.echo("Error: ACUMBAMAIL_EMAIL and ACUMBAMAIL_PASSWORD are required for automation commands", err=True)
        raise SystemExit(1)
    client = AutomationClient(resolved_email, resolved_password)
    client.login()
    return client
```

- [ ] **Step 4: Create `acumbamail/cli/commands/automations.py`**

```python
from __future__ import annotations
from typing import Optional
import typer
import yaml

from acumbamail.cli.utils import get_automation_client, print_json, handle_error

app = typer.Typer(help="Gestión de automatizaciones como código")

_EMAIL_OPT = typer.Option(None, "--email", envvar="ACUMBAMAIL_EMAIL")
_PASS_OPT = typer.Option(None, "--password", envvar="ACUMBAMAIL_PASSWORD")


@app.command("list")
def list_automations(
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Lista todas las automatizaciones."""
    try:
        client = get_automation_client(email, password)
        workflows = client.list_workflows()
        print_json([{"id": w.id, "name": w.name, "description": w.description,
                     "active": w.active, "booting": w.booting} for w in workflows])
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("deploy")
def deploy_automation(
    file: str = typer.Argument(..., help="Ruta al fichero YAML"),
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Despliega una automatización desde YAML (idempotente por nombre)."""
    from acumbamail.automation_yaml import load_yaml, deploy_yaml
    try:
        data = load_yaml(file)
        client = get_automation_client(email, password)
        result = deploy_yaml(data, client)
        print_json(result)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("export")
def export_automation(
    automation_id: Optional[int] = typer.Option(None, "--id"),
    name: Optional[str] = typer.Option(None, "--name"),
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Exporta una automatización existente a formato YAML."""
    from acumbamail.automation_yaml import export_yaml
    try:
        client = get_automation_client(email, password)
        if automation_id is None and name is None:
            typer.echo("Error: provide --id or --name", err=True)
            raise SystemExit(1)
        if automation_id is None:
            match = next((w for w in client.list_workflows() if w.name == name), None)
            if not match:
                typer.echo(f"Error: automation '{name}' not found", err=True)
                raise SystemExit(1)
            automation_id = match.id
        workflow = client.get_workflow(automation_id)
        data = export_yaml(workflow)
        typer.echo(yaml.dump(data, allow_unicode=True, default_flow_style=False))
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("delete")
def delete_automation(
    automation_id: Optional[int] = typer.Option(None, "--id"),
    name: Optional[str] = typer.Option(None, "--name"),
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Elimina una automatización por ID o nombre."""
    try:
        client = get_automation_client(email, password)
        if automation_id is None and name is None:
            typer.echo("Error: provide --id or --name", err=True)
            raise SystemExit(1)
        if automation_id is None:
            match = next((w for w in client.list_workflows() if w.name == name), None)
            if not match:
                typer.echo(f"Error: automation '{name}' not found", err=True)
                raise SystemExit(1)
            automation_id = match.id
        client.delete_workflow(automation_id)
        print_json({"deleted": automation_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)
```

- [ ] **Step 5: Register group in `acumbamail/cli/main.py`**

Add after the webhooks import:

```python
from acumbamail.cli.commands import automations as automations_module
```

Add after `app.add_typer(webhooks_module.app, name="webhooks")`:

```python
app.add_typer(automations_module.app, name="automations")
```

- [ ] **Step 6: Export from `acumbamail/__init__.py`**

Add to the imports and `__all__` in `acumbamail/__init__.py`:

```python
from .automation_client import AutomationClient
from .automation_models import Automation, AutomationNode
```

And add `"AutomationClient"`, `"Automation"`, `"AutomationNode"` to `__all__`.

- [ ] **Step 7: Run all CLI tests — confirm pass**

```bash
uv run pytest tests/test_automation_cli.py -v
```
Expected: all tests pass

- [ ] **Step 8: Run full test suite — confirm no regressions**

```bash
uv run pytest -v
```
Expected: all existing + new tests pass

- [ ] **Step 9: Manual smoke test**

```bash
uv run acumbamail automations --help
uv run acumbamail automations list --help
uv run acumbamail automations deploy --help
```
Expected: help text appears for each command

- [ ] **Step 10: Commit**

```bash
git add acumbamail/cli/commands/automations.py acumbamail/cli/utils.py acumbamail/cli/main.py acumbamail/__init__.py tests/test_automation_cli.py
git commit -m "feat(automations): add automations CLI commands (list, deploy, export, delete)"
```

---

## Task 9: CHANGELOG + version bump

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `acumbamail/__init__.py` (version)

- [ ] **Step 1: Update `CHANGELOG.md`**

Add at the top (before the first existing entry):

```markdown
## [0.3.0] — 2026-05-18

### Added
- `AutomationClient`: new session-based client for the Acumbamail automation API
  (`/automation/api/`). Uses email+password auth (not API token).
- `Automation` and `AutomationNode` dataclasses.
- YAML-as-code support for automations: `load_yaml`, `validate_yaml`,
  `deploy_yaml`, `export_yaml` in `acumbamail.automation_yaml`.
- CLI command group `acumbamail automations` with subcommands:
  - `list` — list all automations as JSON
  - `deploy <file.yaml>` — idempotent deploy (create or update by name)
  - `export --id|--name` — export existing automation to YAML
  - `delete --id|--name` — delete automation
- Claude Code skill `acumbamail/data/skills/acumbamail-automations/SKILL.md`
  with full API reference and examples.
- Auth: `ACUMBAMAIL_EMAIL` + `ACUMBAMAIL_PASSWORD` env vars (or `--email`/`--password` flags).

### Notes
- `pyyaml` promoted from dev-only to main dependency.
- Automation API requires web session auth; public API token does not work.
```

- [ ] **Step 2: Bump version in `acumbamail/__init__.py`**

Change `__version__ = "0.2.0"` to `__version__ = "0.3.0"`.

- [ ] **Step 3: Final test run**

```bash
uv run pytest -v --tb=short
```
Expected: all tests pass

- [ ] **Step 4: Final commit**

```bash
git add CHANGELOG.md acumbamail/__init__.py
git commit -m "chore: bump version to 0.3.0, update CHANGELOG"
```

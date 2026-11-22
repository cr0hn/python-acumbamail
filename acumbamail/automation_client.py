from __future__ import annotations
import re
from typing import Any, Optional
import httpx2
from .automation_models import Automation, AutomationNode
from .utils import ensure_dict

BASE_URL = "https://acumbamail.com"


class AutomationClient:
    def __init__(self, email: str, password: str):
        self._email: Optional[str] = email
        self._password: Optional[str] = password
        self._client = httpx2.Client(follow_redirects=True)
        self._csrf_token: Optional[str] = None

    @classmethod
    def from_session(cls, sessionid: str, csrftoken: str) -> "AutomationClient":
        """Create client from existing session cookies (no login needed)."""
        instance = cls.__new__(cls)
        instance._email = None
        instance._password = None
        instance._csrf_token = csrftoken
        instance._client = httpx2.Client(follow_redirects=False)
        instance._client.cookies.set("sessionid", sessionid, domain="acumbamail.com", path="/")
        instance._client.cookies.set("csrftoken", csrftoken, domain="acumbamail.com", path="/")
        return instance

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
        # GET the login page to extract CSRF token
        resp = self._client.get(f"{BASE_URL}/login/")
        resp.raise_for_status()
        self._csrf_token = self._extract_csrf(resp.text)
        # Acumbamail uses a wizard form: POST to /login/2fa/ with auth-* field names
        resp = self._client.post(
            f"{BASE_URL}/login/2fa/",
            data={
                "csrfmiddlewaretoken": self._csrf_token,
                "login_view-current_step": "auth",
                "auth-username": self._email,
                "auth-password": self._password,
                "google-id-token": "",
            },
            headers={"Referer": f"{BASE_URL}/login/"},
        )
        resp.raise_for_status()
        if not self._client.cookies.get("sessionid"):
            raise ValueError("Login failed: no session cookie received. Check credentials.")
        # Update CSRF token from response if available
        if resp.text:
            try:
                self._csrf_token = self._extract_csrf(resp.text)
            except ValueError:
                pass
        # Use the current CSRF cookie if no newer token found in HTML
        if not self._csrf_token:
            self._csrf_token = self._client.cookies.get("csrftoken", "")

    def _headers(self) -> dict[str, Any]:
        # Prefer current cookie value; include Origin+Referer for Django CSRF validation
        csrf = self._client.cookies.get("csrftoken") or self._csrf_token or ""
        return {
            "X-CSRFToken": csrf,
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/automation/workflow-list",
        }

    def _get(self, path: str) -> httpx2.Response:
        resp = self._client.get(f"{BASE_URL}{path}")
        resp.raise_for_status()
        return resp

    def _post(self, path: str, json: dict[str, Any]) -> httpx2.Response:
        resp = self._client.post(f"{BASE_URL}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp

    def _patch(self, path: str, json: dict[str, Any]) -> httpx2.Response:
        resp = self._client.patch(f"{BASE_URL}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp

    def _put(self, path: str, json: dict[str, Any]) -> httpx2.Response:
        resp = self._client.put(f"{BASE_URL}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp

    def _delete(self, path: str) -> None:
        resp = self._client.delete(f"{BASE_URL}{path}", headers=self._headers())
        resp.raise_for_status()

    def list_workflows(self) -> list[Automation]:
        return [Automation.from_basic_api(item) for item in self._get("/automation/api/basic-workflow/").json()]

    def get_workflow(self, workflow_id: int) -> Automation:
        return Automation.from_full_api(self._get(f"/automation/api/workflow/{workflow_id}/").json())

    def create_workflow(self, name: str, description: Optional[str] = None) -> Automation:
        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        return Automation.from_full_api(self._post("/automation/api/workflow/", payload).json())

    def update_workflow(self, workflow_id: int, *, name: Optional[str] = None, active: Optional[bool] = None) -> Automation:
        if name is None and active is None:
            raise ValueError("At least one of 'name' or 'active' must be provided")
        payload: dict[str, Any] = {}
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

    def create_node(self, node_type: str, workflow_id: int, source_id: str,
                    siblings: Optional[list[Any]] = None, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "sourceId": source_id,
            "nodeType": node_type,
            "workflow": str(workflow_id),
            "siblings": siblings or [],
        }
        if extra:
            payload.update(extra)
        return ensure_dict(self._post(f"/automation/api/{node_type.lower()}/", payload).json())

    def update_node(self, node_type: str, node_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return ensure_dict(self._put(f"/automation/api/{node_type.lower()}/{node_id}/", payload).json())

    def delete_node(self, node_type: str, node_id: str) -> None:
        self._delete(f"/automation/api/{node_type.lower()}/{node_id}/")

    def close(self) -> None:
        client = getattr(self, "_client", None)
        if client is not None:
            client.close()

    def __enter__(self) -> "AutomationClient":
        self.login()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

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
        resp.raise_for_status()
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

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AutomationClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

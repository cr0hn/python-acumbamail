from __future__ import annotations
import json
import os
import sys
from typing import Any

import typer

from acumbamail import AcumbamailClient


def get_client(token: str | None) -> AcumbamailClient:
    resolved = token or os.environ.get("ACUMBAMAIL_TOKEN")
    if not resolved:
        typer.echo("Error: ACUMBAMAIL_TOKEN not set and --token not provided", err=True)
        raise SystemExit(1)
    return AcumbamailClient(auth_token=resolved)


def print_json(data: Any) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, default=str))


def handle_error(e: Exception) -> None:
    typer.echo(f"Error: {e}", err=True)
    raise SystemExit(1)


_SESSION_FILE = os.path.expanduser("~/.config/acumbamail/session.json")


def get_automation_client(email: str | None, password: str | None) -> "AutomationClient":
    from acumbamail.automation_client import AutomationClient
    import json

    # Try stored session first
    if os.path.exists(_SESSION_FILE):
        try:
            with open(_SESSION_FILE) as f:
                session = json.load(f)
            if session.get("sessionid"):
                return AutomationClient.from_session(
                    session["sessionid"], session.get("csrftoken", "")
                )
        except (json.JSONDecodeError, KeyError):
            pass

    # Fall back to email/password programmatic login
    resolved_email = email or os.environ.get("ACUMBAMAIL_EMAIL")
    resolved_password = password or os.environ.get("ACUMBAMAIL_PASSWORD")
    if not resolved_email or not resolved_password:
        typer.echo(
            "Error: run 'acumbamail automations login' first, "
            "or set ACUMBAMAIL_EMAIL and ACUMBAMAIL_PASSWORD",
            err=True,
        )
        raise SystemExit(1)
    client = AutomationClient(resolved_email, resolved_password)
    client.login()
    return client

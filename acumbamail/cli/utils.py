from __future__ import annotations
import json
import os
import sys
from typing import Any, TYPE_CHECKING

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

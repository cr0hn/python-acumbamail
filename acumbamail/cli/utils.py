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

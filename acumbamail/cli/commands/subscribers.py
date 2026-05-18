import json
from pathlib import Path
from typing import Optional

import typer

from acumbamail.cli.utils import get_client, print_json, handle_error

app = typer.Typer(help="Gestión de suscriptores")


@app.command("list")
def list_subscribers(
    list_id: int = typer.Option(..., "--list-id"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Lista suscriptores de una lista."""
    try:
        client = get_client(token)
        subs = client.get_subscribers(list_id)
        print_json([
            {"email": s.email, "list_id": s.list_id, "is_active": s.is_active, "fields": s.fields}
            for s in subs
        ])
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("add")
def add_subscriber(
    list_id: int = typer.Option(..., "--list-id"),
    email: str = typer.Option(..., "--email"),
    fields: Optional[str] = typer.Option(None, "--fields", help="JSON string con campos extra"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Añade un suscriptor a una lista."""
    try:
        parsed_fields = json.loads(fields) if fields else None
        client = get_client(token)
        sub = client.add_subscriber(email=email, list_id=list_id, fields=parsed_fields)
        print_json({"email": sub.email, "list_id": sub.list_id})
    except json.JSONDecodeError:
        typer.echo("Error: --fields debe ser un JSON válido", err=True)
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("delete")
def delete_subscriber(
    list_id: int = typer.Option(..., "--list-id"),
    email: str = typer.Option(..., "--email"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Borra un suscriptor de una lista."""
    try:
        client = get_client(token)
        client.delete_subscriber(email=email, list_id=list_id)
        print_json({"deleted": True, "email": email, "list_id": list_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("search")
def search_subscriber(
    query: str = typer.Option(..., "--query"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Busca un suscriptor en todas las listas."""
    try:
        client = get_client(token)
        results = client.search_subscriber(query)
        print_json([
            {"email": s.email, "status": s.status, "list_id": s.list_id, "id": s.id}
            for s in results
        ])
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("unsubscribe")
def unsubscribe_subscriber(
    list_id: int = typer.Option(..., "--list-id"),
    email: str = typer.Option(..., "--email"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Da de baja a un suscriptor de una lista."""
    try:
        client = get_client(token)
        client.unsubscribe_subscriber(list_id=list_id, email=email)
        print_json({"unsubscribed": True, "email": email, "list_id": list_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("batch-add")
def batch_add_subscribers(
    list_id: int = typer.Option(..., "--list-id"),
    file: Path = typer.Option(..., "--file", exists=True, readable=True),
    update: bool = typer.Option(False, "--update/--no-update", help="Actualizar si ya existe"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Importa suscriptores desde un fichero JSON."""
    try:
        subscribers_data = json.loads(file.read_text())
        client = get_client(token)
        results = client.batch_add_subscribers(
            list_id=list_id,
            subscribers_data=subscribers_data,
            update_subscriber=update,
        )
        print_json([{"email": r.email, "subscriber_id": r.subscriber_id} for r in results])
    except json.JSONDecodeError:
        typer.echo("Error: el fichero debe contener un array JSON válido", err=True)
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

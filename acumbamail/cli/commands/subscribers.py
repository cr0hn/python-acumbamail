import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer

from acumbamail.cli.utils import get_client, print_json, handle_error

app = typer.Typer(help="Gestión de suscriptores")

_STATUS_CHOICES = ("active", "inactive", "all")
_DEFAULT_INACTIVE_DATE_FROM = "2000-01-01"


@app.command("list")
def list_subscribers(
    list_id: int = typer.Option(..., "--list-id"),
    status: str = typer.Option(
        "active",
        "--status",
        help=(
            "'active' (por defecto, comportamiento previo sin cambios) | 'inactive' | 'all'. "
            "AVISO: los inactivos vienen de getInactiveSubscribers, que es GLOBAL DE CUENTA "
            "-- la API de Acumbamail acepta list_id pero lo IGNORA (verificado con una lista "
            "inexistente que devolvio igualmente el total de la cuenta). Con --status inactive/all "
            "puedes recibir inactivos de OTRAS listas, no solo de list_id. No hay forma de que "
            "el CLI ni el SDK filtren esto: es una limitacion de la API."
        ),
    ),
    date_from: Optional[str] = typer.Option(
        None, "--date-from", help="YYYY-MM-DD. Solo aplica con --status inactive/all. Por defecto: 2000-01-01."
    ),
    date_to: Optional[str] = typer.Option(
        None, "--date-to", help="YYYY-MM-DD. Solo aplica con --status inactive/all. Por defecto: hoy."
    ),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Lista suscriptores de una lista.

    Por defecto (--status active) solo devuelve activos, igual que siempre.
    lists list reporta un subscribers_count que SI incluye bajas y bounces:
    comparar ese numero contra esta salida sin --status inactive/all da la
    falsa impresion de que faltan suscriptores.
    """
    try:
        if status not in _STATUS_CHOICES:
            typer.echo(f"Error: --status debe ser uno de {_STATUS_CHOICES}", err=True)
            raise SystemExit(1)

        client = get_client(token)
        out = []

        if status in ("active", "all"):
            subs = client.get_subscribers(list_id)
            out.extend(
                {"email": s.email, "list_id": s.list_id, "is_active": s.is_active, "fields": s.fields}
                for s in subs
            )

        if status in ("inactive", "all"):
            parsed_from = (
                datetime.strptime(date_from, "%Y-%m-%d") if date_from
                else datetime.strptime(_DEFAULT_INACTIVE_DATE_FROM, "%Y-%m-%d")
            )
            parsed_to = datetime.strptime(date_to, "%Y-%m-%d") if date_to else datetime.now()
            inactives = client.get_inactive_subscribers(parsed_from, parsed_to, full_info=True)
            out.extend(
                {
                    "email": i.email,
                    "list_id": None,
                    "is_active": False,
                    "fields": None,
                    "reason": i.reason,
                    "reason_label": i.reason_label.value if i.reason_label else None,
                    "note": "global de cuenta: puede pertenecer a otra lista distinta de list_id",
                }
                for i in inactives
            )

        print_json(out)
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
    """Busca un suscriptor en todas las listas.

    AVISO: no devuelve suscriptores "not verified" (doble opt-in sin
    confirmar), ni siquiera buscando por su email exacto -- verificado contra
    la API real 2026-08-03. Que no aparezca aqui no significa que no exista:
    usa 'subscribers check' para comprobar un email concreto en una lista.
    """
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
        print_json([
            {"email": r.email, "subscriber_id": r.subscriber_id, "status": r.status, "error": r.error}
            for r in results
        ])
    except json.JSONDecodeError:
        typer.echo("Error: el fichero debe contener un array JSON válido", err=True)
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("check")
def check_subscribers(
    list_id: int = typer.Option(..., "--list-id"),
    email: Optional[List[str]] = typer.Option(
        None, "--email", help="Email a comprobar (repetir para varios)"
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", exists=True, readable=True,
        help="Fichero JSON con un array de emails, p.ej. [\"a@x.com\", \"b@x.com\"]",
    ),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Comprueba el estado real de uno o varios emails en una lista, uno a uno.

    Es la unica forma de ver suscriptores "not verified" (doble opt-in sin
    confirmar): ni 'subscribers list', ni 'subscribers search', ni
    get_inactive_subscribers, ni los exports CSV los devuelven. Un email
    "not verified" existe en la lista y no aparece por ninguna otra via del
    CLI ni del SDK -- una auditoria de "quien falta" sin este comando da
    falsos positivos con estos suscriptores.

    Usa getSubscriberDetails por email, así que hace una llamada API por
    cada email: no pensado para listas completas, sino para comprobar
    candidatos concretos.
    """
    try:
        emails = list(email) if email else []
        if file:
            file_data = json.loads(file.read_text())
            if not isinstance(file_data, list):
                typer.echo("Error: --file debe contener un array JSON de emails", err=True)
                raise SystemExit(1)
            emails.extend(file_data)

        if not emails:
            typer.echo("Error: proporciona al menos un --email o --file", err=True)
            raise SystemExit(1)

        client = get_client(token)
        results = []
        for e in emails:
            try:
                details = client.get_subscriber_details(list_id, e)
                results.append({
                    "email": e,
                    "found": True,
                    "status": details.status,
                    "id": details.id,
                    "fields": details.fields,
                })
            except SystemExit:
                raise
            except Exception as exc:
                results.append({"email": e, "found": False, "status": None, "error": str(exc)})

        print_json(results)
    except json.JSONDecodeError:
        typer.echo("Error: --file debe ser un JSON válido", err=True)
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

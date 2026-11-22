import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import typer

from acumbamail.cli.utils import get_client, print_json, handle_error

app = typer.Typer(help="Gestión de suscriptores")

_STATUS_CHOICES = ("active", "inactive")
_DEFAULT_INACTIVE_DATE_FROM = "2000-01-01"

# Los dos estados viven en ambitos distintos y la API no permite reconciliarlos:
# los activos se piden por lista, los inactivos solo a nivel de cuenta. Por eso no
# hay un --status all: sumarlos daria un total que no significa nada.
_SCOPE_ERROR = (
    "Error: --status inactive es de ambito CUENTA y no admite --list-id.\n"
    "  getInactiveSubscribers es global: la API acepta list_id, responde 200 y lo IGNORA\n"
    "  (verificado con una lista inexistente, que devolvio igualmente el total de la cuenta).\n"
    "  Filtrar por lista es imposible: los inactivos vienen con list_id nulo.\n"
    "  Usa 'subscribers list --status inactive' sin --list-id, o 'subscribers check'\n"
    "  para consultar emails concretos de una lista."
)


@app.command("list")
def list_subscribers(
    list_id: Optional[int] = typer.Option(
        None, "--list-id", help="Requerido con --status active. Prohibido con --status inactive."
    ),
    status: str = typer.Option(
        "active",
        "--status",
        help=(
            "'active' (por defecto, comportamiento previo sin cambios) exige --list-id. "
            "'inactive' devuelve bajas y bounces de TODA LA CUENTA y no admite --list-id, "
            "porque la API no permite filtrarlos por lista. No existe 'all': mezclar ambos "
            "seria sumar una lista con la cuenta entera."
        ),
    ),
    date_from: Optional[str] = typer.Option(
        None, "--date-from", help="YYYY-MM-DD. Solo aplica con --status inactive. Por defecto: 2000-01-01."
    ),
    date_to: Optional[str] = typer.Option(
        None, "--date-to", help="YYYY-MM-DD. Solo aplica con --status inactive. Por defecto: hoy."
    ),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
) -> None:
    """Lista suscriptores activos de una lista, o inactivos de toda la cuenta.

    lists list reporta un subscribers_count que SI incluye bajas y bounces, asi que
    comparar ese numero contra los activos de aqui da la falsa impresion de que faltan
    suscriptores. La diferencia son inactivos, y solo se pueden ver a nivel de cuenta.

    Ni siquiera --status inactive lo ve todo: los suscriptores en estado 'not verified'
    (doble opt-in sin confirmar) no salen en ningun listado de la API. Para esos, usa
    subscribers check con los emails concretos.
    """
    try:
        if status not in _STATUS_CHOICES:
            typer.echo(f"Error: --status debe ser uno de {_STATUS_CHOICES}", err=True)
            raise SystemExit(1)

        if status == "active" and list_id is None:
            typer.echo("Error: --status active requiere --list-id", err=True)
            raise SystemExit(1)

        if status == "inactive" and list_id is not None:
            typer.echo(_SCOPE_ERROR, err=True)
            raise SystemExit(1)

        client = get_client(token)
        out: list[dict[str, Any]] = []

        if status == "active" and list_id is not None:
            subs = client.get_subscribers(list_id)
            out.extend(
                {"email": s.email, "list_id": s.list_id, "is_active": s.is_active, "fields": s.fields}
                for s in subs
            )
        else:
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
                    "scope": "account",
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
) -> None:
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
) -> None:
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
) -> None:
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
) -> None:
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
) -> None:
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
) -> None:
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

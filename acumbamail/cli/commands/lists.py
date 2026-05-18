import typer

from acumbamail.cli.utils import get_client, print_json, handle_error

app = typer.Typer(help="Gestión de listas de suscriptores")


@app.command("list")
def list_lists(token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN")):
    """Lista todas las listas disponibles."""
    try:
        client = get_client(token)
        lists = client.get_lists()
        print_json([
            {
                "id": lst.id,
                "name": lst.name,
                "description": lst.description,
                "subscribers_count": lst.subscribers_count,
                "unsubscribed_count": lst.unsubscribed_count,
                "bounced_count": lst.bounced_count,
            }
            for lst in lists
        ])
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("create")
def create_list(
    name: str = typer.Option(..., "--name"),
    sender_email: str = typer.Option(..., "--sender-email"),
    description: str = typer.Option("", "--description"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Crea una nueva lista."""
    try:
        client = get_client(token)
        client.default_sender_email = sender_email
        lst = client.create_list(name=name, description=description)
        print_json({"id": lst.id, "name": lst.name, "description": lst.description})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("delete")
def delete_list(
    list_id: int = typer.Option(..., "--list-id"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Borra una lista."""
    try:
        client = get_client(token)
        client.delete_list(list_id)
        print_json({"deleted": True, "list_id": list_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("stats")
def list_stats(
    list_id: int = typer.Option(..., "--list-id"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Estadísticas de una lista."""
    try:
        client = get_client(token)
        stats = client.get_list_stats(list_id)
        print_json(stats)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

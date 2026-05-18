import typer

from acumbamail.cli.utils import get_client, print_json, handle_error

app = typer.Typer(help="Configuración de webhooks")


@app.command("smtp-get")
def smtp_webhook_get(
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Muestra la configuración del webhook SMTP."""
    try:
        client = get_client(token)
        wh = client.get_smtp_webhook()
        print_json({
            "id": wh.id, "url": wh.url, "active": wh.active,
            "delivered": wh.delivered, "hard_bounces": wh.hard_bounces,
            "soft_bounces": wh.soft_bounces, "complaints": wh.complaints,
            "opens": wh.opens, "clicks": wh.clicks,
        })
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("smtp-config")
def smtp_webhook_config(
    url: str = typer.Option(..., "--url"),
    delivered: bool = typer.Option(False, "--delivered/--no-delivered"),
    hard_bounce: bool = typer.Option(False, "--hard-bounce/--no-hard-bounce"),
    soft_bounce: bool = typer.Option(False, "--soft-bounce/--no-soft-bounce"),
    complain: bool = typer.Option(False, "--complain/--no-complain"),
    opens: bool = typer.Option(False, "--opens/--no-opens"),
    click: bool = typer.Option(False, "--click/--no-click"),
    active: bool = typer.Option(True, "--active/--no-active"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Configura el webhook SMTP."""
    try:
        client = get_client(token)
        webhook_id = client.config_smtp_webhook(
            callback_url=url, delivered=delivered, hard_bounce=hard_bounce,
            soft_bounce=soft_bounce, complain=complain, opens=opens,
            click=click, active=active,
        )
        print_json({"id": webhook_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("list-get")
def list_webhook_get(
    list_id: int = typer.Option(..., "--list-id"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Muestra la configuración del webhook de una lista."""
    try:
        client = get_client(token)
        wh = client.get_list_webhook(list_id)
        print_json({
            "id": wh.id, "url": wh.url, "active": wh.active,
            "subscribes": wh.subscribes, "unsubscribes": wh.unsubscribes,
            "hard_bounces": wh.hard_bounces, "soft_bounces": wh.soft_bounces,
            "complaints": wh.complaints, "opens": wh.opens, "clicks": wh.clicks,
        })
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("list-config")
def list_webhook_config(
    list_id: int = typer.Option(..., "--list-id"),
    url: str = typer.Option(..., "--url"),
    subscribes: bool = typer.Option(False, "--subscribes/--no-subscribes"),
    unsubscribes: bool = typer.Option(False, "--unsubscribes/--no-unsubscribes"),
    hard_bounce: bool = typer.Option(False, "--hard-bounce/--no-hard-bounce"),
    soft_bounce: bool = typer.Option(False, "--soft-bounce/--no-soft-bounce"),
    complain: bool = typer.Option(False, "--complain/--no-complain"),
    opens: bool = typer.Option(False, "--opens/--no-opens"),
    click: bool = typer.Option(False, "--click/--no-click"),
    active: bool = typer.Option(True, "--active/--no-active"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Configura el webhook de una lista."""
    try:
        client = get_client(token)
        webhook_id = client.config_list_webhook(
            list_id=list_id, callback_url=url, subscribes=subscribes,
            unsubscribes=unsubscribes, hard_bounce=hard_bounce, soft_bounce=soft_bounce,
            complain=complain, opens=opens, click=click, active=active,
        )
        print_json({"id": webhook_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

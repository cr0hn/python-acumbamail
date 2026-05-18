import typer

from acumbamail.cli.utils import get_client, print_json, handle_error

app = typer.Typer(help="Gestión de campañas")


@app.command("list")
def list_campaigns(
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Lista todas las campañas."""
    try:
        client = get_client(token)
        campaigns = client.get_campaigns()
        print_json([
            {
                "id": c.id,
                "name": c.name,
                "subject": c.subject,
                "from_email": c.from_email,
                "list_ids": c.list_ids,
            }
            for c in campaigns
        ])
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("info")
def campaign_info(
    campaign_id: int = typer.Option(..., "--campaign-id"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Información básica de una campaña."""
    try:
        client = get_client(token)
        info = client.get_campaign_basic_information(campaign_id)
        print_json(info)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("stats")
def campaign_stats(
    campaign_id: int = typer.Option(..., "--campaign-id"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Estadísticas totales de una campaña."""
    try:
        client = get_client(token)
        stats = client.get_campaign_total_information(campaign_id)
        print_json({
            "total_delivered": stats.total_delivered,
            "emails_to_send": stats.emails_to_send,
            "opened": stats.opened,
            "unique_clicks": stats.unique_clicks,
            "total_clicks": stats.total_clicks,
            "hard_bounces": stats.hard_bounces,
            "soft_bounces": stats.soft_bounces,
            "unsubscribes": stats.unsubscribes,
            "complaints": stats.complaints,
            "unopened": stats.unopened,
            "campaign_url": stats.campaign_url,
        })
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

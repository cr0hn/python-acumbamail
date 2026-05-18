from typing import List, Optional
import typer

from acumbamail.cli.utils import get_client, print_json, handle_error
from acumbamail.exceptions import AcumbamailValidationError, AcumbamailAPIError

app = typer.Typer(help="Gestión de campañas")


@app.command("create")
def create_campaign(
    name: str = typer.Option(..., "--name", help="Nombre interno de la campaña"),
    subject: str = typer.Option(..., "--subject", help="Asunto del email"),
    list_id: List[int] = typer.Option(..., "--list-id", help="ID de lista (repetir para varias)"),
    html_file: Optional[str] = typer.Option(None, "--html-file", help="Ruta al fichero HTML"),
    html: Optional[str] = typer.Option(None, "--html", help="Contenido HTML inline"),
    from_email: Optional[str] = typer.Option(None, "--from-email", help="Email del remitente (debe estar verificado en Acumbamail)"),
    from_name: Optional[str] = typer.Option(None, "--from-name", help="Nombre del remitente"),
    scheduled_at: Optional[str] = typer.Option(None, "--scheduled-at", help="Programar envío: 'YYYY-MM-DD HH:MM'"),
    token: str = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN"),
):
    """Crea y envía una campaña de email.

    El contenido HTML debe incluir el tag *|UNSUBSCRIBE_URL|* para el enlace de baja.

    Ejemplo:
      acumbamail campaigns create --name "Newsletter" --subject "Novedades" \\
        --html-file email.html --list-id 1138335 --from-email sender@domain.com
    """
    try:
        if not html_file and not html:
            typer.echo("Error: indica --html-file o --html", err=True)
            raise SystemExit(1)
        if html_file and html:
            typer.echo("Error: usa --html-file o --html, no los dos a la vez", err=True)
            raise SystemExit(1)

        if html_file:
            try:
                with open(html_file) as f:
                    content = f.read()
            except FileNotFoundError:
                typer.echo(f"Error: no se encontró el fichero '{html_file}'", err=True)
                raise SystemExit(1)
        else:
            content = html

        scheduled = None
        if scheduled_at:
            from datetime import datetime
            try:
                scheduled = datetime.strptime(scheduled_at, "%Y-%m-%d %H:%M")
            except ValueError:
                typer.echo("Error: --scheduled-at debe tener formato 'YYYY-MM-DD HH:MM'", err=True)
                raise SystemExit(1)

        client = get_client(token)
        if from_email:
            client.default_sender_email = from_email
        if from_name:
            client.default_sender_name = from_name

        campaign = client.create_campaign(
            name=name,
            subject=subject,
            content=content,
            list_ids=list_id,
            scheduled_at=scheduled,
        )
        print_json({"id": campaign.id, "name": campaign.name, "subject": campaign.subject,
                    "from_email": campaign.from_email, "list_ids": campaign.list_ids})

    except (AcumbamailValidationError, AcumbamailAPIError) as e:
        msg = str(e)
        if "UNSUBSCRIBE_URL" in msg:
            typer.echo(
                "Error: el HTML no contiene el tag de desuscripción obligatorio.\n"
                "  Añade este enlace en tu HTML:\n"
                "  <a href=\"*|UNSUBSCRIBE_URL|*\">Darse de baja</a>",
                err=True,
            )
        elif "not verified" in msg.lower():
            typer.echo(
                "Error: el email del remitente no está verificado en Acumbamail.\n"
                "  Verifica tu email en: https://acumbamail.com/app/account/senders/\n"
                "  El remitente debe estar verificado antes de enviar campañas.",
                err=True,
            )
        else:
            typer.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


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

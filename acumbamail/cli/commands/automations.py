from __future__ import annotations
from typing import Optional
import typer
import yaml

from acumbamail.cli.utils import get_automation_client, print_json, handle_error
from acumbamail.automation_yaml import load_yaml, deploy_yaml, export_yaml

app = typer.Typer(help="Gestión de automatizaciones como código")

_EMAIL_OPT = typer.Option(None, "--email", envvar="ACUMBAMAIL_EMAIL")
_PASS_OPT = typer.Option(None, "--password", envvar="ACUMBAMAIL_PASSWORD")


@app.command("list")
def list_automations(
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Lista todas las automatizaciones."""
    try:
        client = get_automation_client(email, password)
        workflows = client.list_workflows()
        print_json([{"id": w.id, "name": w.name, "description": w.description,
                     "active": w.active, "booting": w.booting} for w in workflows])
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("deploy")
def deploy_automation(
    file: str = typer.Argument(..., help="Ruta al fichero YAML"),
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Despliega una automatización desde YAML (idempotente por nombre)."""
    try:
        data = load_yaml(file)
        client = get_automation_client(email, password)
        result = deploy_yaml(data, client)
        print_json(result)
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("export")
def export_automation(
    automation_id: Optional[int] = typer.Option(None, "--id"),
    name: Optional[str] = typer.Option(None, "--name"),
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Exporta una automatización existente a formato YAML."""
    try:
        client = get_automation_client(email, password)
        if automation_id is None and name is None:
            typer.echo("Error: provide --id or --name", err=True)
            raise SystemExit(1)
        if automation_id is None:
            match = next((w for w in client.list_workflows() if w.name == name), None)
            if not match:
                typer.echo(f"Error: automation '{name}' not found", err=True)
                raise SystemExit(1)
            automation_id = match.id
        workflow = client.get_workflow(automation_id)
        data = export_yaml(workflow)
        typer.echo(yaml.dump(data, allow_unicode=True, default_flow_style=False))
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("delete")
def delete_automation(
    automation_id: Optional[int] = typer.Option(None, "--id"),
    name: Optional[str] = typer.Option(None, "--name"),
    email: Optional[str] = _EMAIL_OPT,
    password: Optional[str] = _PASS_OPT,
):
    """Elimina una automatización por ID o nombre."""
    try:
        client = get_automation_client(email, password)
        if automation_id is None and name is None:
            typer.echo("Error: provide --id or --name", err=True)
            raise SystemExit(1)
        if automation_id is None:
            match = next((w for w in client.list_workflows() if w.name == name), None)
            if not match:
                typer.echo(f"Error: automation '{name}' not found", err=True)
                raise SystemExit(1)
            automation_id = match.id
        client.delete_workflow(automation_id)
        print_json({"deleted": automation_id})
    except SystemExit:
        raise
    except Exception as e:
        handle_error(e)

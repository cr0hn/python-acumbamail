from __future__ import annotations
from typing import Optional
import typer
import yaml

from acumbamail.cli.utils import get_automation_client, print_json, handle_error
from acumbamail.automation_yaml import load_yaml, deploy_yaml, export_yaml

app = typer.Typer(help="Gestión de automatizaciones como código")

_EMAIL_OPT = typer.Option(None, "--email", envvar="ACUMBAMAIL_EMAIL")
_PASS_OPT = typer.Option(None, "--password", envvar="ACUMBAMAIL_PASSWORD")


@app.command("login")
def login_automation():
    """Abre Chrome para autenticarte con Acumbamail y guarda la sesión."""
    import json
    from pathlib import Path
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        typer.echo("Error: playwright no instalado. Ejecuta: uv add playwright && playwright install chrome", err=True)
        raise SystemExit(1)

    typer.echo("Abriendo Chrome... Inicia sesión en Acumbamail.")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://acumbamail.com/login/")
        try:
            page.wait_for_url("**/app/**", timeout=120_000)
        except Exception:
            typer.echo("Error: tiempo de espera agotado o login cancelado.", err=True)
            browser.close()
            raise SystemExit(1)

        cookies = {c["name"]: c["value"] for c in context.cookies("https://acumbamail.com")}
        browser.close()

    sessionid = cookies.get("sessionid")
    csrftoken = cookies.get("csrftoken", "")
    if not sessionid:
        typer.echo("Error: no se encontró la cookie de sesión tras el login.", err=True)
        raise SystemExit(1)

    session_dir = Path.home() / ".config" / "acumbamail"
    session_dir.mkdir(parents=True, exist_ok=True)
    with open(session_dir / "session.json", "w") as f:
        json.dump({"sessionid": sessionid, "csrftoken": csrftoken}, f)

    print_json({"status": "ok", "message": "Sesión guardada. Ya puedes usar los comandos de automatizaciones."})


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

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
    import platform
    from pathlib import Path

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        typer.echo("Error: playwright no instalado. Ejecuta: pip install playwright && playwright install chrome", err=True)
        raise SystemExit(1)

    # Perfil dedicado para este CLI — no toca el Chrome del usuario
    profile_dir = Path.home() / ".config" / "acumbamail" / "chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    typer.echo("Abriendo Chrome...")
    typer.echo("→ Inicia sesión en Acumbamail en la ventana que se abre.")
    typer.echo("→ Espera a que cargue la página principal (puede tardar ~20s en detectarse).")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
            ignore_default_args=["--no-sandbox"],
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
        )
        page = context.new_page() if not context.pages else context.pages[0]
        page.goto("https://acumbamail.com/login/")
        page.bring_to_front()
        try:
            # Espera hasta que el usuario llegue a la app (no solo salga de /login)
            page.wait_for_url("**/app/**", timeout=300_000)
        except Exception:
            typer.echo("Tiempo de espera agotado o login cancelado.", err=True)
            context.close()
            raise SystemExit(1)

        # Verificar que la sesión funciona realmente contra la API
        typer.echo("Login detectado, verificando sesión...")
        api_page = context.new_page()
        api_page.goto("https://acumbamail.com/automation/api/basic-workflow/")
        api_ok = '"id"' in api_page.content()
        all_cookies = {c["name"]: c["value"] for c in context.cookies("https://acumbamail.com")}
        context.close()

    if not api_ok:
        typer.echo("Error: el login no se completó correctamente. Inténtalo de nuevo.", err=True)
        raise SystemExit(1)

    sessionid = all_cookies.get("sessionid")
    csrftoken = all_cookies.get("csrftoken", "")
    if not sessionid:
        typer.echo("Error: no se encontró la cookie de sesión. Inténtalo de nuevo.", err=True)
        raise SystemExit(1)

    # Guardar TODAS las cookies de acumbamail para máxima compatibilidad
    session_dir = Path.home() / ".config" / "acumbamail"
    session_dir.mkdir(parents=True, exist_ok=True)
    with open(session_dir / "session.json", "w") as f:
        json.dump({"sessionid": sessionid, "csrftoken": csrftoken,
                   "backend": all_cookies.get("backend", "py3")}, f)

    print_json({"status": "ok", "message": "Sesión guardada en ~/.config/acumbamail/session.json"})


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

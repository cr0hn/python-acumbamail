import os
from typing import Optional

import typer

from acumbamail.cli.commands import lists as lists_module
from acumbamail.cli.commands import subscribers as subscribers_module
from acumbamail.cli.commands import campaigns as campaigns_module
from acumbamail.cli.commands import webhooks as webhooks_module
from acumbamail.cli.commands import automations as automations_module
from acumbamail.cli.commands.install_skills import install_skills

app = typer.Typer(help="Acumbamail CLI — gestión de email marketing")

app.add_typer(lists_module.app, name="lists")
app.add_typer(subscribers_module.app, name="subscribers")
app.add_typer(campaigns_module.app, name="campaigns")
app.add_typer(webhooks_module.app, name="webhooks")
app.add_typer(automations_module.app, name="automations")
app.command("install-skills")(install_skills)


@app.callback()
def main(
    token: Optional[str] = typer.Option(None, "--token", envvar="ACUMBAMAIL_TOKEN", help="API token"),
):
    if token:
        os.environ["ACUMBAMAIL_TOKEN"] = token

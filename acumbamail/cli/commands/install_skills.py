import shutil
from pathlib import Path

import typer

SKILL_NAME = "acumbamail-cli"


def _skill_source() -> Path:
    import acumbamail.data.skills as _pkg
    pkg_file = getattr(_pkg, "__file__", None)
    if pkg_file is None:
        raise RuntimeError("Cannot locate bundled skills: package has no __file__")
    return Path(pkg_file).parent / SKILL_NAME


def install_skills(
    global_install: bool = typer.Option(False, "--global", "-g", help="Install globally (~/.claude/skills/)"),
):
    """Install Acumbamail CLI skills for Claude Code."""
    if global_install:
        target_dir = Path.home() / ".claude" / "skills" / SKILL_NAME
    else:
        target_dir = Path.cwd() / ".claude" / "skills" / SKILL_NAME

    source = _skill_source()

    if not source.exists():
        typer.echo(f"Error: bundled skill not found at {source}", err=True)
        raise SystemExit(1)

    if target_dir.exists():
        shutil.rmtree(target_dir)

    shutil.copytree(source, target_dir)

    scope = "global" if global_install else "local"
    typer.echo(f"Skill '{SKILL_NAME}' installed {scope}ly → {target_dir}")

"""Router command: print routing prompt for skill directory."""
from __future__ import annotations

from pathlib import Path
import click
from .. import workspace


@click.command(help="Print a name+description router prompt for LLMs without native skills.")
@click.argument("path", type=click.Path(path_type=Path))
def router(path: Path) -> None:
    try:
        click.echo(workspace.router_prompt(workspace.load(path)))
    except workspace.WorkspaceError:
        click.echo(workspace.router_prompt(path))

"""Init command: scaffold workspace and copy source PDF into stage 01."""
from __future__ import annotations

from pathlib import Path
import click
from .. import workspace
from ._common import new_cb


@click.command(help="Create a workspace and copy the source PDF into stage 01.")
@click.argument("name", type=click.Path(path_type=Path), callback=new_cb)
@click.option("--source", type=click.Path(path_type=Path, dir_okay=False), required=True)
def init(name: Path, source: Path) -> None:
    if source.suffix.lower() != ".pdf":
        raise click.BadParameter("source must be a .pdf file", param_hint="--source")
    w = workspace.scaffold(name, source)
    click.echo(f"Workspace created at {w.root}")

"""Export command: copy finished skills to target directory."""
from __future__ import annotations

from pathlib import Path

import click

from .. import workspace
from ._common import ws_cb


@click.command(help="Copy finished skill folders to a skills directory (needs stages 05 and 06 done).")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
@click.option("--dest", type=click.Path(path_type=Path), default=Path.home() / ".claude" / "skills",
              show_default=True)
def export(ws: Path, dest: Path) -> None:
    for t in workspace.export_skills(workspace.load(ws), dest):
        click.echo(f"exported {t}")

"""Status command: show stage states and gate approvals."""
from __future__ import annotations

from pathlib import Path
import click
from .. import workspace
from ..console import console, is_interactive, status_table
from ._common import ws_cb


@click.command(help="Show stage state and gate approvals.")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
def status(ws: Path) -> None:
    w = workspace.load(ws)
    if not is_interactive():
        click.echo("\n".join(w.status()))
        return
    rows = []
    for s in workspace.STAGES:
        state = "done" if w.done(s) else "pending"
        gate = ""
        if s in workspace.GATES:
            gate = "[green]APPROVED[/]" if w.approved(s) else "[red]awaiting approval[/]"
        rows.append((s, state, gate))
    t = status_table(rows)
    if t is not None:
        console.print(t)
    else:
        click.echo("\n".join(w.status()))

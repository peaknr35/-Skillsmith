"""Audit command: verify section coverage ledger, unit accounting, and exposure."""
from __future__ import annotations

from pathlib import Path
import click
from .. import workspace
from ._common import ws_cb


@click.command("audit", help="Audit a run: section coverage ledger, stage-03->04 unit accounting, procedural "
                            "exposure check, and lexical step-to-page citation support per unit.")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
def audit_cmd(ws: Path) -> None:
    from .. import audit
    rep = audit.audit_workspace(workspace.load(ws))
    click.echo(rep.summary())
    click.echo(rep.markdown())
    if not rep.ok:
        raise click.exceptions.Exit(1)

"""Verify command: mechanical citation check for numbers."""
from __future__ import annotations

from pathlib import Path
import click
from .. import verify, workspace
from ._common import ws_cb


@click.command("verify", help="Mechanical citation check: every number in generated skills must appear in a "
                             "page-cited unit. It cannot prove a claim is faithful; review evidence by hand.")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
def verify_cmd(ws: Path) -> None:
    rep = verify.check(workspace.load(ws))
    click.echo(rep.summary())
    if rep.unsourced:
        raise click.exceptions.Exit(1)

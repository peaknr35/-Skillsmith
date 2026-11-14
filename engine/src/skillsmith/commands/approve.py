"""Approve command: mark a human review gate approved."""
from __future__ import annotations

from pathlib import Path
import click
from .. import gates, workspace
from ._common import ws_cb


@click.command(help="Mark a review gate approved. This is a human action; the runner never does it.")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
@click.argument("stage")
def approve(ws: Path, stage: str) -> None:
    gates.approve(workspace.load(ws), stage)
    click.echo(f"{stage} approved")

"""Config command: inspect effective Skillsmith configuration and layer resolution."""
from __future__ import annotations

import click

from ..config import KEYS, load_settings
from ..console import console, is_interactive, kv_table


@click.command("config", help="Show active configuration, resolved layers, and any syntax/path warnings.")
@click.pass_context
def config_cmd(ctx: click.Context) -> None:
    cfg_path = ctx.obj.get("config_path") if ctx.obj else None
    s = load_settings(cfg_path)
    shown = {"provider": s.provider, "model": s.model or "(provider default)",
             "base_url": s.base_url or "(default)", "runs_dir": s.runs_dir or "(auto-detect)"}
    if is_interactive():
        t = kv_table("Effective Configuration", list(shown.items()))
        if t is not None:
            console.print(t)
    else:
        for k in KEYS:
            click.echo(f"{k} = {getattr(s, k)}")
    for w in s.warnings:
        click.echo(f"WARN: {w}", err=True)

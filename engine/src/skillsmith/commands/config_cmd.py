"""Config command: inspect effective Skillsmith configuration and layer resolution."""
from __future__ import annotations

from pathlib import Path
import click
from ..config import load_settings
from ..console import console, is_interactive, kv_table


@click.command("config", help="Show active configuration, resolved layers, and any syntax/path warnings.")
@click.pass_context
def config_cmd(ctx: click.Context) -> None:
    cfg_path = ctx.obj.get("config_path") if ctx.obj else None
    s = load_settings(cfg_path)
    if is_interactive():
        rows = [
            ("provider", s.provider),
            ("model", s.model),
            ("base_url", s.base_url or "(default)"),
            ("runs_dir", s.runs_dir or "(auto-detect)"),
            ("max_chunk_tokens", str(s.max_chunk_tokens)),
            ("chunk_overlap_tokens", str(s.chunk_overlap_tokens)),
            ("max_retries", str(s.max_retries)),
        ]
        t = kv_table("Effective Configuration", rows)
        if t is not None:
            console.print(t)
    else:
        for k in ["provider", "model", "base_url", "runs_dir", "max_chunk_tokens", "chunk_overlap_tokens", "max_retries"]:
            click.echo(f"{k} = {getattr(s, k)}")
    for w in s.warnings:
        click.echo(f"WARN: {w}", err=True)

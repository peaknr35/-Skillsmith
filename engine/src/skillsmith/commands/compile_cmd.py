"""Compile command: compile workspace artifacts through stage 05."""
from __future__ import annotations

from pathlib import Path
import click
from .. import gates, runner, workspace
from ..console import spinner
from ._common import LLM_STAGES, load_dotenv, ws_cb


@click.command("compile", help="Compile workspace stages non-interactively through stage 05 (fails if review gates are unapproved).")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "langchain", "fake"]))
@click.option("--model", help="model name; for langchain use 'provider:model'")
def compile_cmd(ws: Path, provider: str, model: str | None) -> None:
    from .. import cli
    w = workspace.load(ws)
    load_dotenv(Path.cwd(), ws, ws.parent)
    prov = cli.get_provider(provider, model)
    for stage in ["01_ingest", "02_map", "03_extract", "04_consolidate", "05_write"]:
        if w.done(stage):
            continue
        if gates.is_gate(stage) and not w.approved(stage):
            raise click.ClickException(f"Gate {stage} is pending approval; run: skillsmith approve {ws} {stage}")
        with spinner(f"Compiling {stage}..."):
            runner.run_stage(w, stage, prov if stage in LLM_STAGES else None)
        click.echo(f"{stage} done")
    click.echo(f"Compilation complete through stage 05 for {ws}")

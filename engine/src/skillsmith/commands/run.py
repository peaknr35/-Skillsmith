"""Run command: execute the NEXT pending stage or a specified --stage."""
from __future__ import annotations

from pathlib import Path
import click
from .. import gates, runner, workspace
from ..console import spinner
from ._common import LLM_STAGES, load_dotenv, ws_cb


@click.command(help="Run the NEXT pending stage (or --stage). One stage per call; stops at review gates.")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
@click.option("--stage", help="e.g. 02_map")
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "langchain", "fake"]))
@click.option("--model", help="model name; for langchain use 'provider:model'")
def run(ws: Path, stage: str | None, provider: str, model: str | None) -> None:
    from .. import cli
    w = workspace.load(ws)
    stage = stage or w.next_pending()
    if stage is None:
        click.echo("All stages complete.")
        return
    if stage in LLM_STAGES:
        load_dotenv(Path.cwd(), ws, ws.parent)
    prov = cli.get_provider(provider, model) if stage in LLM_STAGES else None
    with spinner(f"Running stage {stage}..."):
        out = runner.run_stage(w, stage, prov)
    click.echo(f"{stage} done: {out}")
    if gates.is_gate(stage):
        click.echo(f"REVIEW GATE: review {out}, then: skillsmith approve {ws} {stage}")

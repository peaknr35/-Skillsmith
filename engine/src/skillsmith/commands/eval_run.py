"""Eval-run command: trigger tests and task comparison."""
from __future__ import annotations

from pathlib import Path

import click

from .. import workspace
from ._common import load_dotenv, ws_cb


@click.command("eval-run", help="Run the stage-06 tests against a real model: trigger test, then with/without-skill "
                                "task comparison (raw outputs saved under stages/06_eval/runs/).")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
@click.option("--skill", help="skill name (default: the first one)")
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "langchain", "fake"]))
@click.option("--model")
@click.option("--parts", default="both", type=click.Choice(["both", "triggers", "tasks"]))
@click.option("--with-playbook", is_flag=True, help="also put playbook.md in the treatment context (default: SKILL.md only)")
def eval_run(ws: Path, skill: str | None, provider: str, model: str | None, parts: str, with_playbook: bool) -> None:
    from .. import cli, evalrun
    w = workspace.load(ws)
    load_dotenv(Path.cwd(), ws, ws.parent)
    prov = cli.get_provider(provider, model)
    run_dir = evalrun.run(w, prov, skill, str(model or getattr(prov, "model", "") or ""), with_playbook, parts)
    click.echo(f"eval run saved: {run_dir}")
    click.echo((run_dir / "report.md").read_text(encoding="utf-8"))

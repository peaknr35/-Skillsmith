"""Eval-quality command: blind A/B comparative judging."""
from __future__ import annotations

from pathlib import Path

import click

from .. import workspace
from ._common import build_provider, load_dotenv, ws_cb


@click.command("eval-quality", help="Blind answer-quality comparison: repeated with/without-skill answers, judged "
                                    "in random order on generic criteria (solves the problem, fits constraints, risks, "
                                    "actionability, honesty). Never mentions the skill to the judge.")
@click.argument("ws", type=click.Path(path_type=Path), callback=ws_cb)
@click.option("--skill", help="skill name (default: the first one)")
@click.option("--provider", default=None, type=click.Choice(["anthropic", "openai", "langchain"]),
              help="default: SKILLSMITH_PROVIDER, then the config file, then anthropic")
@click.option("--model", help="generator model")
@click.option("--judge-model", help="judge model (default: same as the generator; a different one is more independent)")
@click.option("--repeats", default=3, show_default=True, type=click.IntRange(1, 10))
@click.option("--skill-only", is_flag=True, help="treatment gets SKILL.md only (default: SKILL.md + playbook.md)")
@click.option("--workers", default=4, show_default=True, type=click.IntRange(1, 8))
@click.option("--eval-file", type=click.Path(path_type=Path, exists=True, dir_okay=False),
              help="judge on a frozen eval.json (use after rebuilding the skill, so before/after share the same tasks)")
@click.pass_context
def eval_quality(ctx: click.Context, ws: Path, skill: str | None, provider: str | None, model: str | None,
                 judge_model: str | None, repeats: int, skill_only: bool, workers: int,
                 eval_file: Path | None) -> None:
    from .. import evalquality
    w = workspace.load(ws)
    load_dotenv(Path.cwd(), ws, ws.parent)
    gen = build_provider(ctx, provider, model)
    judge = build_provider(ctx, provider, judge_model) if judge_model else gen
    run_dir = evalquality.run(w, gen, judge, skill, str(model or getattr(gen, "model", "") or ""),
                              str(judge_model or getattr(judge, "model", "") or ""), repeats, not skill_only, workers, eval_file)
    click.echo(f"quality run saved: {run_dir}")
    click.echo((run_dir / "report.md").read_text(encoding="utf-8"))

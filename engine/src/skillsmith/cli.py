"""skillsmith CLI (Click). Rich gives tables and colour on a terminal; output is plain when piped."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from . import gates, runner, verify, workspace
from .llm import get_provider

LLM_STAGES = ("02_map", "03_extract", "04_consolidate", "06_eval")


def _rich():
    if not sys.stdout.isatty():
        return None
    try:
        from rich.console import Console
        return Console()
    except ImportError:  # pragma: no cover
        return None


def load_dotenv(*dirs: Path) -> list[Path]:
    """Load KEY=VALUE lines from .env files into os.environ without overriding variables
    that are already set. Values are never printed. Returns the files that were read."""
    import os
    read = []
    candidates = []
    for base in dirs:  # each folder and up to four parents, nearest first, so one .env can serve engine/ and runs/
        b = Path(base).resolve()
        candidates += [b, *list(b.parents)[:4]]
    for d in candidates:
        f = Path(d) / ".env"
        if not f.is_file() or f in read:
            continue
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip().removeprefix("export ").strip()
            val = val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            if key and key not in os.environ:
                os.environ[key] = val
        read.append(f)
    return read


def runs_dir() -> Path | None:
    """Where bare run names live: $SKILLSMITH_RUNS_DIR, else the nearest `runs` folder at or above the
    current directory (up to five levels)."""
    import os
    env = os.environ.get("SKILLSMITH_RUNS_DIR")
    if env:
        return Path(env)
    here = Path.cwd().resolve()
    for d in [here, *list(here.parents)[:5]]:
        if (d / "runs").is_dir():
            return d / "runs"
    return None


def _is_bare(p: Path) -> bool:
    return len(p.parts) == 1 and not p.is_absolute() and p.anchor == ""


def resolve_ws(p: Path) -> Path:
    """An existing path wins; a bare name (icm-paper) is looked up in the runs folder."""
    if p.exists() or not _is_bare(p):
        return p
    r = runs_dir()
    return (r / p) if r and (r / p).exists() else p


def resolve_new(p: Path) -> Path:
    """For init: a bare name is created inside the runs folder when there is one."""
    r = runs_dir()
    return (r / p) if _is_bare(p) and r else p


def _ws_cb(ctx, param, value):
    return resolve_ws(value)


def _new_cb(ctx, param, value):
    return resolve_new(value)


@click.group(help="Forge agent skills from papers, articles and books.")
def cli() -> None:
    pass


@cli.command(help="Create a workspace and copy the source PDF into stage 01.")
@click.argument("name", type=click.Path(path_type=Path), callback=_new_cb)
@click.option("--source", type=click.Path(path_type=Path, dir_okay=False), required=True)
def init(name: Path, source: Path) -> None:
    w = workspace.scaffold(name, source)
    click.echo(f"Workspace created at {w.root}")


@cli.command(help="Run the NEXT pending stage (or --stage). One stage per call; stops at review gates.")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
@click.option("--stage", help="e.g. 02_map")
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "langchain"]))
@click.option("--model", help="model name; for langchain use 'provider:model'")
def run(ws: Path, stage: str | None, provider: str, model: str | None) -> None:
    w = workspace.load(ws)
    stage = stage or w.next_pending()
    if stage is None:
        click.echo("All stages complete.")
        return
    if stage in LLM_STAGES:
        load_dotenv(Path.cwd(), ws, ws.parent)  # a .env next to the run, or in the folder you launch from
    prov = get_provider(provider, model) if stage in LLM_STAGES else None
    out = runner.run_stage(w, stage, prov)
    click.echo(f"{stage} done: {out}")
    if gates.is_gate(stage):
        click.echo(f"REVIEW GATE: review {out}, then: skillsmith approve {ws} {stage}")


@cli.command(help="Mark a review gate approved. This is a human action; the runner never does it.")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
@click.argument("stage")
def approve(ws: Path, stage: str) -> None:
    gates.approve(workspace.load(ws), stage)
    click.echo(f"{stage} approved")


@cli.command(help="Show stage state and gate approvals.")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
def status(ws: Path) -> None:
    w = workspace.load(ws)
    con = _rich()
    if con is None:
        click.echo("\n".join(w.status()))
        return
    from rich.table import Table
    t = Table("stage", "state", "gate")
    for s in workspace.STAGES:
        state = "[green]done[/]" if w.done(s) else "[yellow]pending[/]"
        gate = ""
        if s in workspace.GATES:
            gate = "[green]APPROVED[/]" if w.approved(s) else "[red]awaiting approval[/]"
        t.add_row(s, state, gate)
    con.print(t)


@cli.command("verify", help="Mechanical citation check: every number in generated skills must appear in a "
                            "page-cited unit. It cannot prove a claim is faithful; review evidence by hand.")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
def verify_cmd(ws: Path) -> None:
    rep = verify.check(workspace.load(ws))
    click.echo(rep.summary())
    if rep.unsourced:
        raise click.exceptions.Exit(1)


@cli.command("audit", help="Audit a run: section coverage ledger, stage-03->04 unit accounting, procedural "
                           "exposure check, and lexical step-to-page citation support per unit.")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
def audit_cmd(ws: Path) -> None:
    from . import audit
    rep = audit.audit_workspace(workspace.load(ws))
    click.echo(rep.summary())
    click.echo(rep.markdown())
    if not rep.ok:
        raise click.exceptions.Exit(1)


@cli.command(help="Copy finished skill folders to a skills directory (needs stages 05 and 06 done).")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
@click.option("--dest", type=click.Path(path_type=Path), default=Path.home() / ".claude" / "skills",
              show_default=True)
def export(ws: Path, dest: Path) -> None:
    for t in workspace.export_skills(workspace.load(ws), dest):
        click.echo(f"exported {t}")


@cli.command(help="Print a name+description router prompt for LLMs without native skills.")
@click.argument("path", type=click.Path(path_type=Path))
def router(path: Path) -> None:
    try:
        click.echo(workspace.router_prompt(workspace.load(path)))
    except workspace.WorkspaceError:
        click.echo(workspace.router_prompt(path))


@cli.command("eval-run", help="Run the stage-06 tests against a real model: trigger test, then with/without-skill "
                              "task comparison (raw outputs saved under stages/06_eval/runs/).")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
@click.option("--skill", help="skill name (default: the first one)")
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "langchain"]))
@click.option("--model")
@click.option("--parts", default="both", type=click.Choice(["both", "triggers", "tasks"]))
@click.option("--with-playbook", is_flag=True, help="also put playbook.md in the treatment context (default: SKILL.md only)")
def eval_run(ws: Path, skill: str | None, provider: str, model: str | None, parts: str, with_playbook: bool) -> None:
    from . import evalrun
    w = workspace.load(ws)
    load_dotenv(Path.cwd(), ws, ws.parent)
    prov = get_provider(provider, model)
    run_dir = evalrun.run(w, prov, skill, model or getattr(prov, "model", ""), with_playbook, parts)
    click.echo(f"eval run saved: {run_dir}")
    click.echo((run_dir / "report.md").read_text(encoding="utf-8"))


@cli.command("eval-quality", help="Blind answer-quality comparison: repeated with/without-skill answers, judged "
                                  "in random order on generic criteria (solves the problem, fits constraints, risks, "
                                  "actionability, honesty). Never mentions the skill to the judge.")
@click.argument("ws", type=click.Path(path_type=Path), callback=_ws_cb)
@click.option("--skill", help="skill name (default: the first one)")
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "langchain"]))
@click.option("--model", help="generator model")
@click.option("--judge-model", help="judge model (default: same as the generator; a different one is more independent)")
@click.option("--repeats", default=3, show_default=True, type=click.IntRange(1, 10))
@click.option("--skill-only", is_flag=True, help="treatment gets SKILL.md only (default: SKILL.md + playbook.md)")
@click.option("--workers", default=4, show_default=True, type=click.IntRange(1, 8))
@click.option("--eval-file", type=click.Path(path_type=Path, exists=True, dir_okay=False),
              help="judge on a frozen eval.json (use after rebuilding the skill, so before/after share the same tasks)")
def eval_quality(ws: Path, skill: str | None, provider: str, model: str | None, judge_model: str | None,
                 repeats: int, skill_only: bool, workers: int, eval_file: Path | None) -> None:
    from . import evalquality
    w = workspace.load(ws)
    load_dotenv(Path.cwd(), ws, ws.parent)
    gen = get_provider(provider, model)
    judge = get_provider(provider, judge_model) if judge_model else gen
    run_dir = evalquality.run(w, gen, judge, skill, model or getattr(gen, "model", ""),
                              judge_model or getattr(judge, "model", ""), repeats, not skill_only, workers, eval_file)
    click.echo(f"quality run saved: {run_dir}")
    click.echo((run_dir / "report.md").read_text(encoding="utf-8"))


@cli.command("mcp-serve", help="Serve an exported skills directory over MCP (stdio).")
@click.argument("skills_dir", type=click.Path(path_type=Path, exists=True, file_okay=False))
def mcp_serve(skills_dir: Path) -> None:
    from .mcp_server import serve
    serve(skills_dir)


def evalrun_error():
    from .evalrun import EvalRunError
    return EvalRunError


def main(argv=None) -> int:
    """Entry point. Exit codes: 0 ok, 1 error/failed check, 2 abstain or usage error."""
    try:
        rv = cli.main(args=argv, standalone_mode=False)
        return int(rv) if isinstance(rv, int) else 0
    except click.exceptions.Exit as e:
        return int(e.exit_code)
    except click.ClickException as e:
        e.show()
        return 2
    except evalrun_error() as e:
        click.echo(f"ERROR: {e}", err=True)
        return 1
    except runner.StageAbstain as e:
        click.echo(f"ABSTAIN: {e}", err=True)
        return 2
    except (runner.StageError, gates.GateError, workspace.WorkspaceError, RuntimeError, ValueError) as e:
        click.echo(f"ERROR: {e}", err=True)
        return 1


def entry() -> None:  # console_scripts target
    raise SystemExit(main())


if __name__ == "__main__":
    entry()

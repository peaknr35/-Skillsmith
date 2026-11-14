"""Skillsmith CLI. Commands live in skillsmith.commands and are registered here.
Rich gives tables and colour on a terminal; output is plain when piped.
"""
from __future__ import annotations

import sys
from pathlib import Path
import click

from . import gates, runner, verify, workspace
from .commands import ALL
from .commands._common import (
    LLM_STAGES,
    load_dotenv,
    runs_dir,
    resolve_ws,
    resolve_new,
    ws_cb,
    new_cb,
)
from .llm import get_provider
from .console import is_interactive, console


def _rich():
    if not is_interactive():
        return None
    return console


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Forge agent skills from papers, articles and books.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to skillsmith.toml (falls back to ./skillsmith.toml, then user config).",
)
@click.pass_context
def cli(ctx: click.Context, config_path: Path | None) -> None:
    """Skillsmith: from 'we found' to 'do this'."""
    ctx.obj = {"config_path": config_path}


# Register all subcommands from the commands package
for _cmd in ALL:
    cli.add_command(_cmd)


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

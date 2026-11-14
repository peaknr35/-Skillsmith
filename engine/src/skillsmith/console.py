"""Rich console: theme, custom spinner, reusable tables, and non-TTY fallback."""
from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Generator

try:
    from rich.console import Console
    from rich.table import Table
    from rich.theme import Theme

    THEME = Theme({
        "ok": "bold green",
        "warn": "yellow",
        "err": "bold red",
        "stage": "cyan",
        "dim": "dim",
    })
    console = Console(theme=THEME)
    err_console = Console(stderr=True, theme=THEME)
    HAS_RICH = True
except ImportError:  # pragma: no cover
    console = None
    err_console = None
    HAS_RICH = False

SPINNER = "dots12"


def is_interactive() -> bool:
    return HAS_RICH and sys.stdout.isatty()


@contextmanager
def spinner(message: str) -> Generator[None, None, None]:
    if is_interactive():
        with console.status(f"[stage]{message}[/]", spinner=SPINNER):
            yield
    else:
        yield


def kv_table(title: str, rows: list[tuple[str, str]]) -> Table | None:
    if not HAS_RICH:
        return None
    t = Table(title=title, show_lines=False)
    t.add_column("Item", style="stage")
    t.add_column("Value")
    for k, v in rows:
        t.add_row(k, str(v))
    return t


def status_table(rows: list[tuple[str, str, str]]) -> Table | None:
    if not HAS_RICH:
        return None
    t = Table(title="Workspace status")
    t.add_column("Stage", style="stage")
    t.add_column("State")
    t.add_column("Gate")
    for stage, state, gate in rows:
        style = {"done": "ok", "pending": "warn"}.get(state, "dim")
        t.add_row(stage, f"[{style}]{state}[/]", gate)
    return t

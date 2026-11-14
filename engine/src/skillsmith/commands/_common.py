"""Shared helpers, path callbacks, and environment loaders for Skillsmith CLI commands."""
from __future__ import annotations

import os
from pathlib import Path

LLM_STAGES = ("02_map", "03_extract", "04_consolidate", "06_eval")


def load_dotenv(*dirs: Path) -> list[Path]:
    """Load KEY=VALUE lines from .env files into os.environ without overriding variables
    that are already set. Values are never printed. Returns the files that were read."""
    read = []
    candidates = []
    for base in dirs:
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


def ws_cb(ctx, param, value):
    return resolve_ws(value) if value is not None else None


def new_cb(ctx, param, value):
    return resolve_new(value) if value is not None else None

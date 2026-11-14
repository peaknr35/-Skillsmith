"""TOML configuration with automatic fallback resolution.

Precedence (highest first): CLI flags > SKILLSMITH_* environment variables > a file given with --config >
./skillsmith.toml > ~/.config/skillsmith/config.toml > defaults.

Every key is checked on its own, so one bad value never discards the rest of a file. Warnings name the
key and the reason but never repeat the value (config files can sit next to secrets).
Missing default files are ignored; a --config file that does not exist is a warning.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib

PROVIDERS = ("anthropic", "openai", "langchain")
KEYS = ("provider", "model", "base_url", "runs_dir")


class Settings(BaseModel):
    provider: str = "anthropic"
    model: str | None = None  # None: the provider's own default
    base_url: str | None = None
    runs_dir: str | None = None
    warnings: list[str] = Field(default_factory=list, exclude=True)


def user_config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "skillsmith" / "config.toml"


def _read(p: Path, warnings: list[str], *, required: bool = False) -> dict[str, Any]:
    if not p.is_file():
        if required:
            warnings.append(f"Config file not found: {p}")
        return {}
    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
        table = data.get("skillsmith", data)
        return dict(table) if isinstance(table, dict) else {}
    except (tomllib.TOMLDecodeError, OSError) as e:
        warnings.append(f"Ignored {p}: {type(e).__name__}")
        return {}


def _check(key: str, value: Any) -> str | None:
    """None when the value is acceptable, otherwise a short reason (never the value itself)."""
    if key not in KEYS:
        return "unknown setting"
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty string"
    if key == "provider" and value not in PROVIDERS:
        return f"must be one of {', '.join(PROVIDERS)}"
    return None


def load_settings(path: Path | None = None, **overrides: Any) -> Settings:
    warnings: list[str] = []
    layers: list[tuple[str, dict[str, Any]]] = [
        (f"user config {user_config_path()}", _read(user_config_path(), warnings)),
        ("./skillsmith.toml", _read(Path("skillsmith.toml"), warnings)),
    ]
    if path is not None:
        layers.append((f"--config {path}", _read(path, warnings, required=True)))
    layers.append(("environment", {k: os.environ[f"SKILLSMITH_{k.upper()}"]
                                   for k in KEYS if f"SKILLSMITH_{k.upper()}" in os.environ}))
    layers.append(("command line", {k: v for k, v in overrides.items() if v is not None}))
    data: dict[str, Any] = {}
    for label, layer in layers:
        for key, value in layer.items():
            reason = _check(key, value)
            if reason:
                warnings.append(f"Ignored '{key}' from {label}: {reason}")
            else:
                data[key] = value
    s = Settings(**data)
    s.warnings = warnings
    return s

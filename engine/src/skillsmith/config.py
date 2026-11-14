"""TOML configuration with automatic fallback resolution.
Precedence: CLI flags > SKILLSMITH_* env vars > ./skillsmith.toml > ~/.config/skillsmith/config.toml > defaults.
Missing files are ignored; unreadable or invalid files or values are skipped with recorded warnings.
"""
from __future__ import annotations

import os
from pathlib import Path

import tomllib
from pydantic import BaseModel, Field, ValidationError

PROVIDERS = ("fake", "anthropic", "openai", "langchain")


class Settings(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5"
    base_url: str | None = None
    runs_dir: str | None = None
    max_chunk_tokens: int = Field(1500, ge=200, le=8000)
    chunk_overlap_tokens: int = Field(100, ge=0, le=1000)
    max_retries: int = Field(2, ge=0, le=5)
    warnings: list[str] = Field(default_factory=list, exclude=True)


def user_config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "skillsmith" / "config.toml"


def _read(p: Path, warnings: list[str]) -> dict:
    if not p.is_file():
        return {}
    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
            return dict(data.get("skillsmith", data))
    except (tomllib.TOMLDecodeError, OSError) as e:
        warnings.append(f"Ignored {p}: {e}")
        return {}


def load_settings(path: Path | None = None, **overrides) -> Settings:
    warnings: list[str] = []
    layers: list[dict] = [
        _read(user_config_path(), warnings),
        _read(path or Path("skillsmith.toml"), warnings),
    ]
    env = {
        k: os.environ[f"SKILLSMITH_{k.upper()}"]
        for k in Settings.model_fields
        if k != "warnings" and f"SKILLSMITH_{k.upper()}" in os.environ
    }
    layers += [env, {k: v for k, v in overrides.items() if v is not None}]
    data: dict = {}
    for layer in layers:
        trial = {**data, **layer}
        try:
            s = Settings(**trial)
            if s.provider not in PROVIDERS:
                raise ValueError(f"provider must be one of {PROVIDERS}")
            data = trial
        except (ValidationError, ValueError) as e:
            warnings.append(f"Ignored invalid settings {layer}: {str(e).splitlines()[0]}")
    s = Settings(**data)
    s.warnings = warnings
    return s

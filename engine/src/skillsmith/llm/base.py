from __future__ import annotations

import math
import os
from typing import Callable, Protocol


class TruncatedOutput(RuntimeError):
    """The model hit its token limit before finishing; the JSON would be cut off."""


def optional_float(name: str, *, minimum: float = 0.0, allow_equal: bool = True) -> float | None:
    """A finite float from the environment, or None when unset or empty.
    A bad value is an explicit error that names the variable (never a traceback from deeper in)."""
    v = os.environ.get(name)
    if v is None or v.strip() == "":
        return None
    try:
        x = float(v)
    except ValueError as e:
        raise RuntimeError(f"{name} must be a number, got {v!r}") from e
    if not math.isfinite(x):
        raise RuntimeError(f"{name} must be a finite number, got {v!r}")
    if x < minimum or (x == minimum and not allow_equal):
        rel = ">=" if allow_equal else ">"
        raise RuntimeError(f"{name} must be {rel} {minimum:g}, got {v!r}")
    return x


def optional_int(name: str) -> int | None:
    """A positive whole number from the environment, or None when unset or empty."""
    v = os.environ.get(name)
    if v is None or v.strip() == "":
        return None
    try:
        n = int(v.strip())
    except ValueError as e:
        raise RuntimeError(f"{name} must be a whole number, got {v!r}") from e
    if n <= 0:
        raise RuntimeError(f"{name} must be a positive whole number, got {v!r}")
    return n


def env_temperature() -> float | None:
    return optional_float("SKILLSMITH_TEMPERATURE", minimum=0.0)


def env_timeout() -> float | None:
    return optional_float("SKILLSMITH_TIMEOUT", minimum=0.0, allow_equal=False)


def check_positive(name: str, value: float | None, *, integer: bool = False) -> None:
    """Validate a value passed in code (not the environment); None means unset."""
    if value is None:
        return
    if integer and (isinstance(value, bool) or not isinstance(value, int)):
        raise RuntimeError(f"{name} must be a whole number, got {value!r}")
    if not math.isfinite(value) or value <= 0:
        raise RuntimeError(f"{name} must be a positive number, got {value!r}")


class Provider(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class FakeProvider:
    """Test double: `responder(system, user) -> str`. Records every call."""

    def __init__(self, responder: Callable[[str, str], str]):
        self.responder = responder
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.responder(system, user)

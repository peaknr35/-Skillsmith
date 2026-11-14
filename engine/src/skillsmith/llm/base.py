from __future__ import annotations

import os
from typing import Callable, Protocol


class TruncatedOutput(RuntimeError):
    """The model hit its token limit before finishing; the JSON would be cut off."""


def optional_float(name: str) -> float | None:
    """A float from the environment, or None when unset. A bad value is an explicit error."""
    v = os.environ.get(name)
    if v in (None, ""):
        return None
    try:
        return float(v)
    except ValueError as e:
        raise RuntimeError(f"{name} must be a number, got {v!r}") from e


def optional_int(name: str) -> int | None:
    v = optional_float(name)
    return None if v is None else int(v)


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

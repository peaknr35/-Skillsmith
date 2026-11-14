from __future__ import annotations

from typing import Callable, Protocol


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

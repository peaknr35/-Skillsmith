from __future__ import annotations

import os
from typing import Any

from .base import TruncatedOutput, optional_float

__all__ = ["AnthropicProvider", "TruncatedOutput"]  # TruncatedOutput stays importable from here


class AnthropicProvider:
    """Optional knobs, unset by default so no model receives a parameter it may reject:
    SKILLSMITH_TEMPERATURE, SKILLSMITH_TIMEOUT (seconds). SKILLSMITH_MAX_TOKENS defaults to 32000."""

    def __init__(self, model: str | None = None, max_tokens: int | None = None,
                 temperature: float | None = None, timeout: float | None = None):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("pip install 'skillsmith[anthropic]'") from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.timeout = timeout if timeout is not None else optional_float("SKILLSMITH_TIMEOUT")
        kw: dict[str, Any] = {"timeout": self.timeout} if self.timeout else {}
        self.client = anthropic.Anthropic(max_retries=5, **kw)
        self.model = model or os.environ.get("SKILLSMITH_MODEL", "claude-sonnet-5-5")
        self.max_tokens = max_tokens or int(os.environ.get("SKILLSMITH_MAX_TOKENS", "32000"))
        self.temperature = temperature if temperature is not None else optional_float("SKILLSMITH_TEMPERATURE")

    def complete(self, system: str, user: str) -> str:
        # Streaming: large max_tokens requests must stream. Stage 04 re-emits whole units,
        # so replies can be long; a truncated reply is an explicit error, never a silent cut.
        kw: dict[str, Any] = {}
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        with self.client.messages.stream(
            model=self.model, max_tokens=self.max_tokens, system=system,
            messages=[{"role": "user", "content": user}], **kw,
        ) as stream:
            msg = stream.get_final_message()
        if getattr(msg, "stop_reason", None) == "max_tokens":
            raise TruncatedOutput(
                f"model output hit the {self.max_tokens}-token limit and was cut off; raise SKILLSMITH_MAX_TOKENS "
                "or lower runner.BATCH_TOKENS so each call consolidates fewer units")
        return "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")

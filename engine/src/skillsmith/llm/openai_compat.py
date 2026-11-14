from __future__ import annotations

import os
from typing import Any

from .base import TruncatedOutput, check_positive, env_temperature, env_timeout, optional_int


class OpenAICompatProvider:
    """OpenAI API or any compatible server (Ollama: base_url=http://localhost:11434/v1).

    Optional knobs, all unset by default so no server receives a parameter it may reject:
    SKILLSMITH_MAX_TOKENS, SKILLSMITH_TEMPERATURE, SKILLSMITH_TIMEOUT (seconds)."""

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 max_tokens: int | None = None, temperature: float | None = None,
                 timeout: float | None = None):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("pip install 'skillsmith[openai]'") from e
        check_positive("timeout", timeout)
        check_positive("max_tokens", max_tokens, integer=True)
        self.timeout = timeout if timeout is not None else env_timeout()
        kw: dict[str, Any] = {"timeout": self.timeout} if self.timeout else {}
        self.client = OpenAI(base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
                             api_key=os.environ.get("OPENAI_API_KEY", "not-needed-for-local"), **kw)
        resolved = model or os.environ.get("SKILLSMITH_MODEL")
        if not resolved:
            raise RuntimeError("pass --model or set SKILLSMITH_MODEL")
        self.model: str = resolved
        self.max_tokens = max_tokens if max_tokens is not None else optional_int("SKILLSMITH_MAX_TOKENS")
        self.temperature = temperature if temperature is not None else env_temperature()

    def complete(self, system: str, user: str) -> str:
        kw: dict[str, Any] = {}
        if self.max_tokens:
            kw["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
        choice = r.choices[0]
        if getattr(choice, "finish_reason", None) == "length":
            raise TruncatedOutput(
                "model output hit the token limit and was cut off; raise SKILLSMITH_MAX_TOKENS "
                "(and check the model's own output limit)")
        return choice.message.content or ""

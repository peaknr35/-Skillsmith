from __future__ import annotations

import os


class TruncatedOutput(RuntimeError):
    """The model hit max_tokens before finishing; the JSON would be cut off."""


class AnthropicProvider:
    def __init__(self, model: str | None = None, max_tokens: int | None = None):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("pip install 'skillsmith[anthropic]'") from e
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(max_retries=5)
        self.model = model or os.environ.get("SKILLSMITH_MODEL", "claude-sonnet-5-5")
        self.max_tokens = max_tokens or int(os.environ.get("SKILLSMITH_MAX_TOKENS", "32000"))

    def complete(self, system: str, user: str) -> str:
        # Streaming: large max_tokens requests must stream. Stage 04 re-emits whole units,
        # so replies can be long; a truncated reply is an explicit error, never a silent cut.
        with self.client.messages.stream(
            model=self.model, max_tokens=self.max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        if getattr(msg, "stop_reason", None) == "max_tokens":
            raise TruncatedOutput(
                f"model output hit the {self.max_tokens}-token limit and was cut off; raise SKILLSMITH_MAX_TOKENS "
                "or lower runner.BATCH_TOKENS so each call consolidates fewer units")
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

from __future__ import annotations

import os


class OpenAICompatProvider:
    """OpenAI API or any compatible server (Ollama: base_url=http://localhost:11434/v1)."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("pip install 'skillsmith[openai]'") from e
        self.client = OpenAI(base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
                             api_key=os.environ.get("OPENAI_API_KEY", "not-needed-for-local"))
        self.model = model or os.environ.get("SKILLSMITH_MODEL")
        if not self.model:
            raise RuntimeError("pass --model or set SKILLSMITH_MODEL")

    def complete(self, system: str, user: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return r.choices[0].message.content or ""

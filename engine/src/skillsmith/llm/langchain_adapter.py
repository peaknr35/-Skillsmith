"""LangChain adapter. Imports langchain lazily; the core never requires it."""
from __future__ import annotations


class LangChainProvider:
    """Wrap any LangChain chat model. Pass a model object, or a 'provider:model' string."""

    def __init__(self, model: object | str):
        if isinstance(model, str):
            try:
                from langchain.chat_models import init_chat_model
            except ImportError as e:  # pragma: no cover
                raise RuntimeError("pip install 'skillsmith[langchain]'") from e
            provider, _, name = model.partition(":")
            model = init_chat_model(name, model_provider=provider)
        self.model = model

    def complete(self, system: str, user: str) -> str:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            msgs = [SystemMessage(content=system), HumanMessage(content=user)]
        except ImportError:  # duck-typed models (tests) accept plain tuples
            msgs = [("system", system), ("human", user)]
        out = self.model.invoke(msgs)
        content = getattr(out, "content", out)
        if isinstance(content, list):
            content = "".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content)
        return str(content)

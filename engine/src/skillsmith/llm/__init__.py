from .base import FakeProvider, Provider


def get_provider(name: str, model: str | None = None, base_url: str | None = None) -> Provider:
    if name == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(model)
    if name == "openai":
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider(model, base_url=base_url) if base_url else OpenAICompatProvider(model)
    if name == "langchain":
        from .langchain_adapter import LangChainProvider
        if not model:
            raise RuntimeError("--model 'provider:model' is required for langchain")
        return LangChainProvider(model)
    raise ValueError(f"unknown provider {name!r} (anthropic, openai, langchain)")


__all__ = ["FakeProvider", "Provider", "get_provider"]

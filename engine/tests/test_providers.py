"""Provider behaviour with the vendor SDKs stubbed (no network, no key), and PDF handle hygiene."""
import sys
import types

import pymupdf
import pytest

from skillsmith.ingest import IngestAbstain, ingest_pdf
from skillsmith.llm.anthropic_provider import AnthropicProvider
from skillsmith.llm.base import TruncatedOutput
from skillsmith.llm.openai_compat import OpenAICompatProvider

NS = types.SimpleNamespace


def install(monkeypatch, name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    monkeypatch.setitem(sys.modules, name, mod)


# ---------------------------------------------------------------- OpenAI-compatible
def fake_openai(monkeypatch, content="hi", finish="stop"):
    seen = {}

    class Completions:
        def create(self, **kw):
            seen["create"] = kw
            return NS(choices=[NS(message=NS(content=content), finish_reason=finish)])

    class Client:
        def __init__(self, **kw):
            seen["init"] = kw
            self.chat = NS(completions=Completions())

    install(monkeypatch, "openai", OpenAI=Client)
    return seen


def clear_knobs(monkeypatch):
    for k in ("SKILLSMITH_MAX_TOKENS", "SKILLSMITH_TEMPERATURE", "SKILLSMITH_TIMEOUT", "SKILLSMITH_MODEL",
              "OPENAI_BASE_URL"):
        monkeypatch.delenv(k, raising=False)


def test_openai_sends_no_optional_parameters_by_default(monkeypatch):
    clear_knobs(monkeypatch)
    seen = fake_openai(monkeypatch)
    p = OpenAICompatProvider(model="llama3", base_url="http://localhost:11434/v1")
    assert p.complete("s", "u") == "hi"
    assert seen["init"]["base_url"] == "http://localhost:11434/v1" and "timeout" not in seen["init"]
    assert seen["create"]["model"] == "llama3"
    assert "max_tokens" not in seen["create"] and "temperature" not in seen["create"]  # servers may reject them


def test_openai_optional_knobs_come_from_env_or_arguments(monkeypatch):
    clear_knobs(monkeypatch)
    monkeypatch.setenv("SKILLSMITH_MAX_TOKENS", "123")
    monkeypatch.setenv("SKILLSMITH_TEMPERATURE", "0")
    monkeypatch.setenv("SKILLSMITH_TIMEOUT", "45")
    seen = fake_openai(monkeypatch)
    OpenAICompatProvider(model="m").complete("s", "u")
    assert seen["create"]["max_tokens"] == 123 and seen["create"]["temperature"] == 0.0  # 0 is a real value
    assert seen["init"]["timeout"] == 45.0
    seen2 = fake_openai(monkeypatch)
    OpenAICompatProvider(model="m", max_tokens=7, temperature=0.5).complete("s", "u")
    assert seen2["create"]["max_tokens"] == 7 and seen2["create"]["temperature"] == 0.5


def test_openai_truncation_is_an_explicit_error(monkeypatch):
    clear_knobs(monkeypatch)
    fake_openai(monkeypatch, content='{"half": ', finish="length")
    with pytest.raises(TruncatedOutput, match="cut off"):
        OpenAICompatProvider(model="m").complete("s", "u")


def test_openai_none_content_is_empty_and_model_is_required(monkeypatch):
    clear_knobs(monkeypatch)
    fake_openai(monkeypatch, content=None)
    assert OpenAICompatProvider(model="m").complete("s", "u") == ""
    with pytest.raises(RuntimeError, match="model"):
        OpenAICompatProvider()


def test_a_bad_numeric_setting_is_an_explicit_error(monkeypatch):
    clear_knobs(monkeypatch)
    monkeypatch.setenv("SKILLSMITH_TEMPERATURE", "warm")
    fake_openai(monkeypatch)
    with pytest.raises(RuntimeError, match="SKILLSMITH_TEMPERATURE must be a number"):
        OpenAICompatProvider(model="m")


# ---------------------------------------------------------------- Anthropic
def fake_anthropic(monkeypatch, stop="end_turn"):
    seen = {}

    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_final_message(self):
            return NS(stop_reason=stop, content=[NS(type="text", text="ok"), NS(type="tool_use", text="X")])

    class Messages:
        def stream(self, **kw):
            seen["stream"] = kw
            return Stream()

    class Client:
        def __init__(self, **kw):
            seen["init"] = kw
            self.messages = Messages()

    install(monkeypatch, "anthropic", Anthropic=Client)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    return seen


def test_anthropic_sends_no_temperature_or_timeout_unless_set(monkeypatch):
    clear_knobs(monkeypatch)
    seen = fake_anthropic(monkeypatch)
    assert AnthropicProvider(model="m").complete("s", "u") == "ok"  # text blocks only
    assert "temperature" not in seen["stream"] and "timeout" not in seen["init"]
    assert seen["init"]["max_retries"] == 5 and seen["stream"]["max_tokens"] == 32000


def test_anthropic_temperature_and_timeout_pass_through_when_set(monkeypatch):
    clear_knobs(monkeypatch)
    monkeypatch.setenv("SKILLSMITH_TEMPERATURE", "0")
    monkeypatch.setenv("SKILLSMITH_TIMEOUT", "90")
    seen = fake_anthropic(monkeypatch)
    AnthropicProvider(model="m").complete("s", "u")
    assert seen["stream"]["temperature"] == 0.0 and seen["init"]["timeout"] == 90.0


def test_anthropic_truncation_still_raises_and_the_class_is_shared(monkeypatch):
    from skillsmith.llm.anthropic_provider import TruncatedOutput as FromAnthropicModule
    assert FromAnthropicModule is TruncatedOutput  # one class, importable from either place
    clear_knobs(monkeypatch)
    fake_anthropic(monkeypatch, stop="max_tokens")
    with pytest.raises(TruncatedOutput):
        AnthropicProvider(model="m").complete("s", "u")


# ---------------------------------------------------------------- PDF handle hygiene
def _spy_on_open(monkeypatch):
    opened = []
    real = pymupdf.open

    def spy(*a, **k):
        d = real(*a, **k)
        opened.append(d)
        return d

    monkeypatch.setattr(pymupdf, "open", spy)
    return opened


def test_pdf_handle_is_closed_after_ingest(monkeypatch, sample_pdf):
    opened = _spy_on_open(monkeypatch)
    ingest_pdf(sample_pdf)
    assert opened and all(d.is_closed for d in opened)


def test_pdf_handle_is_closed_when_ingest_abstains(monkeypatch, scanned_pdf):
    opened = _spy_on_open(monkeypatch)
    with pytest.raises(IngestAbstain):
        ingest_pdf(scanned_pdf)
    assert opened and all(d.is_closed for d in opened)

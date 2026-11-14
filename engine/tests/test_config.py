"""Tests for config loading and cascading fallbacks."""
from skillsmith.config import load_settings


def test_defaults():
    s = load_settings()
    assert s.provider == "anthropic" and s.warnings == []


def test_file_then_flag_override(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nmodel = "m1"\nmax_chunk_tokens = 900\n', encoding="utf-8")
    s = load_settings(p, model="m2")
    assert (s.model, s.max_chunk_tokens) == ("m2", 900)


def test_env_beats_file(tmp_path, monkeypatch):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nprovider = "openai"\n', encoding="utf-8")
    monkeypatch.setenv("SKILLSMITH_PROVIDER", "fake")
    assert load_settings(p).provider == "fake"


def test_invalid_toml_falls_back(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("this is = = not toml", encoding="utf-8")
    s = load_settings(p)
    assert s.provider == "anthropic" and any("Ignored" in w for w in s.warnings)


def test_invalid_value_falls_back(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nmax_chunk_tokens = 5\nmodel = "ok"\n', encoding="utf-8")
    s = load_settings(p)
    assert s.max_chunk_tokens == 1500 and s.warnings


def test_unknown_provider_ignored(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nprovider = "nope"\n', encoding="utf-8")
    assert load_settings(p).provider == "anthropic"


def test_user_config_used(tmp_path, monkeypatch):
    cfg = tmp_path / "xdg" / "skillsmith"
    cfg.mkdir(parents=True)
    (cfg / "config.toml").write_text('[skillsmith]\nmodel = "from-user"\n', encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert load_settings().model == "from-user"

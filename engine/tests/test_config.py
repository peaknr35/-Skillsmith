"""Tests for config loading: per-key validation, layering, and no value leaks in warnings."""
import pytest

from skillsmith.config import PROVIDERS, load_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for k in ("SKILLSMITH_PROVIDER", "SKILLSMITH_MODEL", "SKILLSMITH_BASE_URL", "SKILLSMITH_RUNS_DIR"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-user-config"))
    monkeypatch.chdir(tmp_path)  # so a stray ./skillsmith.toml cannot leak in


def test_defaults():
    s = load_settings()
    assert s.provider == "anthropic" and s.model is None and s.warnings == []


def test_fake_is_not_a_provider():
    assert "fake" not in PROVIDERS


def test_file_then_flag_override(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nmodel = "m1"\nprovider = "openai"\n', encoding="utf-8")
    s = load_settings(p, model="m2")
    assert (s.model, s.provider) == ("m2", "openai")


def test_env_beats_file(tmp_path, monkeypatch):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nprovider = "openai"\n', encoding="utf-8")
    monkeypatch.setenv("SKILLSMITH_PROVIDER", "langchain")
    assert load_settings(p).provider == "langchain"


def test_invalid_toml_falls_back_without_echoing_content(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("secret = = not toml", encoding="utf-8")
    s = load_settings(p)
    assert s.provider == "anthropic" and any("Ignored" in w for w in s.warnings)
    assert not any("secret" in w for w in s.warnings)


def test_one_bad_key_keeps_the_rest_of_the_file(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nprovider = "nope"\nmodel = "ok-model"\n', encoding="utf-8")
    s = load_settings(p)
    assert s.model == "ok-model" and s.provider == "anthropic"
    assert any("'provider'" in w for w in s.warnings)


def test_warnings_never_repeat_the_value(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[skillsmith]\nprovider = "sk-ant-SECRETVALUE"\nbase_url = 12\nsurprise = "x"\n', encoding="utf-8")
    s = load_settings(p)
    text = " ".join(s.warnings)
    assert "SECRETVALUE" not in text
    assert "'provider'" in text and "'base_url'" in text and "'surprise'" in text


def test_missing_explicit_config_warns_and_still_layers_over_local_file(tmp_path):
    (tmp_path / "skillsmith.toml").write_text('model = "from-local"\n', encoding="utf-8")
    s = load_settings(tmp_path / "nofile.toml")
    assert s.model == "from-local"  # the local file is still honoured
    assert any("not found" in w for w in s.warnings)


def test_explicit_config_beats_local_file(tmp_path):
    (tmp_path / "skillsmith.toml").write_text('model = "from-local"\n', encoding="utf-8")
    p = tmp_path / "x.toml"
    p.write_text('model = "from-explicit"\n', encoding="utf-8")
    assert load_settings(p).model == "from-explicit"


def test_user_config_used(tmp_path, monkeypatch):
    cfg = tmp_path / "xdg" / "skillsmith"
    cfg.mkdir(parents=True)
    (cfg / "config.toml").write_text('[skillsmith]\nmodel = "from-user"\n', encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert load_settings().model == "from-user"

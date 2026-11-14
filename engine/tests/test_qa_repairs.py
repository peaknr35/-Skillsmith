"""Regression tests for the independent QA findings (provider flag, gate errors, env validation, config wiring)."""
import pytest
from click.testing import CliRunner

from skillsmith import cli, workspace
from skillsmith.llm import FakeProvider
from skillsmith.llm.base import check_positive, optional_float, optional_int


def _clean(monkeypatch):
    for k in ("SKILLSMITH_PROVIDER", "SKILLSMITH_MODEL", "SKILLSMITH_BASE_URL", "SKILLSMITH_RUNS_DIR",
              "SKILLSMITH_MAX_TOKENS", "SKILLSMITH_TEMPERATURE", "SKILLSMITH_TIMEOUT", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(k, raising=False)


# ---- B1: the unsupported "fake" provider is not offered
@pytest.mark.parametrize("cmd", ["run", "compile", "eval-run", "eval-quality"])
def test_fake_is_not_a_cli_choice(cmd, ws, monkeypatch):
    _clean(monkeypatch)
    r = CliRunner().invoke(cli.cli, [cmd, str(ws.root), "--provider", "fake"])
    assert r.exit_code == 2 and "fake" in r.output  # click rejects it as an invalid choice


# ---- B2: compile with an unapproved gate behaves like run (exit 1, ERROR)
def test_compile_gate_error_exit_code_matches_run(ws, monkeypatch, capsys):
    _clean(monkeypatch)
    monkeypatch.setattr(cli, "get_provider", lambda *a, **k: FakeProvider(lambda s, u: "{}"))
    assert cli.main(["run", str(ws.root)]) == 0  # 01 ingest
    rc = cli.main(["compile", str(ws.root)])
    err = capsys.readouterr().err
    assert rc == 1 and "ERROR" in err


# ---- B3: prerequisite problems are reported before provider/key problems
def test_run_reports_missing_prereq_before_missing_key(ws, monkeypatch, capsys):
    _clean(monkeypatch)
    assert cli.main(["run", str(ws.root), "--stage", "03_extract"]) == 1
    err = capsys.readouterr().err
    assert "not done" in err and "ANTHROPIC_API_KEY" not in err


def test_compile_does_not_need_a_key_when_blocked_by_a_gate(ws, monkeypatch, capsys):
    _clean(monkeypatch)
    assert cli.main(["run", str(ws.root)]) == 0
    monkeypatch.setattr(cli, "get_provider", lambda *a, **k: (_ for _ in ()).throw(AssertionError("built early")))
    rc = cli.main(["compile", str(ws.root)])
    assert rc == 1 and "pending approval" in capsys.readouterr().err  # gate error, no provider built


# ---- B4: a mistyped bare run name says where it looked
def test_bare_name_typo_says_where_it_looked(tmp_path, monkeypatch, capsys):
    _clean(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SKILLSMITH_RUNS_DIR", str(tmp_path / "myruns"))
    assert cli.main(["status", "typo-run"]) == 1
    err = capsys.readouterr().err
    assert "typo-run" in err and "myruns" in err and "current folder" in err


# ---- C4/C5: config values actually reach the provider factory
def test_config_file_supplies_provider_model_and_base_url(ws, tmp_path, monkeypatch):
    _clean(monkeypatch)
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "c.toml"
    cfg.write_text('[skillsmith]\nprovider = "openai"\nmodel = "llama3"\nbase_url = "http://localhost:11434/v1"\n',
                   encoding="utf-8")
    seen = {}

    def fake_get(name, model=None, **kw):
        seen.update(name=name, model=model, **kw)
        return FakeProvider(lambda s, u: "{}")

    monkeypatch.setattr(cli, "get_provider", fake_get)
    cli.main(["--config", str(cfg), "run", str(ws.root)])  # 01 ingest needs no LLM
    cli.main(["--config", str(cfg), "run", str(ws.root)])  # 02 map builds the provider (then fails on "{}")
    assert seen == {"name": "openai", "model": "llama3", "base_url": "http://localhost:11434/v1"}


def test_flag_beats_config_for_provider(ws, tmp_path, monkeypatch):
    _clean(monkeypatch)
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "c.toml"
    cfg.write_text('provider = "openai"\n', encoding="utf-8")
    seen = {}
    monkeypatch.setattr(cli, "get_provider", lambda name, model=None, **k: seen.update(name=name) or FakeProvider(lambda s, u: "{}"))
    cli.main(["--config", str(cfg), "run", str(ws.root)])
    cli.main(["--config", str(cfg), "run", str(ws.root), "--provider", "langchain", "--model", "p:m"])
    assert seen["name"] == "langchain"


def test_config_runs_dir_resolves_bare_names(tmp_path, monkeypatch, sample_pdf):
    _clean(monkeypatch)
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "c.toml"
    cfg.write_text(f'runs_dir = "{(tmp_path / "elsewhere").as_posix()}"\n', encoding="utf-8")
    (tmp_path / "elsewhere").mkdir()
    r = CliRunner().invoke(cli.cli, ["--config", str(cfg), "init", "r1", "--source", str(sample_pdf)])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "elsewhere" / "r1").is_dir()
    assert workspace.load(tmp_path / "elsewhere" / "r1")


# ---- F1/F2: strict env validation naming the variable
@pytest.mark.parametrize("val", ["inf", "-inf", "nan", "0", "-5", "1.5", "abc"])
def test_max_tokens_rejects_bad_values(monkeypatch, val):
    monkeypatch.setenv("SKILLSMITH_MAX_TOKENS", val)
    with pytest.raises(RuntimeError, match="SKILLSMITH_MAX_TOKENS"):
        optional_int("SKILLSMITH_MAX_TOKENS")


def test_empty_env_means_unset(monkeypatch):
    monkeypatch.setenv("SKILLSMITH_MAX_TOKENS", "  ")
    monkeypatch.setenv("SKILLSMITH_TEMPERATURE", "")
    assert optional_int("SKILLSMITH_MAX_TOKENS") is None
    assert optional_float("SKILLSMITH_TEMPERATURE") is None


@pytest.mark.parametrize("val", ["inf", "nan", "-0.1"])
def test_temperature_rejects_non_finite_or_negative(monkeypatch, val):
    monkeypatch.setenv("SKILLSMITH_TEMPERATURE", val)
    with pytest.raises(RuntimeError, match="SKILLSMITH_TEMPERATURE"):
        optional_float("SKILLSMITH_TEMPERATURE", minimum=0.0)


def test_timeout_must_be_positive(monkeypatch):
    monkeypatch.setenv("SKILLSMITH_TIMEOUT", "0")
    with pytest.raises(RuntimeError, match="SKILLSMITH_TIMEOUT"):
        optional_float("SKILLSMITH_TIMEOUT", minimum=0.0, allow_equal=False)


def test_explicit_zero_max_tokens_is_an_error_not_unset():
    with pytest.raises(RuntimeError, match="max_tokens"):
        check_positive("max_tokens", 0, integer=True)


def test_anthropic_provider_rejects_bad_max_tokens_env(monkeypatch):
    import sys
    import types
    mod = types.ModuleType("anthropic")
    mod.Anthropic = lambda **kw: object()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "anthropic", mod)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("SKILLSMITH_MAX_TOKENS", "inf")
    from skillsmith.llm.anthropic_provider import AnthropicProvider
    with pytest.raises(RuntimeError, match="SKILLSMITH_MAX_TOKENS"):
        AnthropicProvider()

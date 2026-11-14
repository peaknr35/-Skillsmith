"""Tests for modular Click commands and config CLI integration."""
from click.testing import CliRunner

from skillsmith.cli import cli


def test_cli_help_lists_all_commands():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    expected_commands = [
        "init",
        "run",
        "approve",
        "status",
        "verify",
        "audit",
        "compile",
        "export",
        "router",
        "eval-run",
        "eval-quality",
        "mcp-serve",
        "config",
    ]
    for cmd in expected_commands:
        assert cmd in result.output, f"Missing command {cmd} in --help"


def test_cli_config_command(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["config"])
    assert result.exit_code == 0
    assert "provider" in result.output


def test_cli_config_flag_with_invalid_toml(tmp_path):
    runner = CliRunner()
    bad_toml = tmp_path / "bad.toml"
    bad_toml.write_text("not = [valid toml", encoding="utf-8")
    result = runner.invoke(cli, ["--config", str(bad_toml), "config"])
    assert result.exit_code == 0
    assert "provider" in result.output


def test_cli_init_requires_pdf_extension(tmp_path):
    runner = CliRunner()
    txt = tmp_path / "doc.txt"
    txt.write_text("some content", encoding="utf-8")
    result = runner.invoke(cli, ["init", str(tmp_path / "ws"), "--source", str(txt)])
    assert result.exit_code != 0
    assert "source must be a .pdf file" in result.output


def test_cli_eval_quality_help_has_baseline_source():
    runner = CliRunner()
    result = runner.invoke(cli, ["eval-quality", "--help"])
    assert result.exit_code == 0
    assert "--baseline-source" in result.output


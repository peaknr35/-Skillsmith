"""End-to-end (fake LLM), CLI, MCP, providers, router."""
import asyncio
import json
import sys

import pytest

from skillsmith import cli, gates, runner, verify, workspace
from skillsmith.llm import FakeProvider, get_provider
from skillsmith.llm.langchain_adapter import LangChainProvider

from .fakes import NAME, fake


def run_all(ws):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    runner.run_stage(ws, "03_extract", prov)
    runner.run_stage(ws, "04_consolidate", prov)
    gates.approve(ws, "04_consolidate")
    runner.run_stage(ws, "05_write")
    runner.run_stage(ws, "06_eval", prov)
    return prov


# ---- AC15
def test_end_to_end_with_fake_provider(ws, tmp_path):
    run_all(ws)
    assert ws.next_pending() is None
    assert verify.check(ws).unsourced == []
    assert (ws.output("05_write") / "verify-report.md").is_file()
    dirs = ws.skill_dirs()
    assert [d.name for d in dirs] == [NAME]
    assert (ws.output("06_eval") / "evals" / NAME / "triggers.md").read_text().count("fire prompt") == 10
    dest = tmp_path / "skills"
    out = workspace.export_skills(ws, dest)
    assert (out[0] / "tool.json").is_file()
    with pytest.raises(workspace.WorkspaceError, match="overwrite"):
        workspace.export_skills(ws, dest)


def test_export_refuses_before_eval(ws, tmp_path):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    with pytest.raises(workspace.WorkspaceError):
        workspace.export_skills(ws, tmp_path / "x")


def test_consolidate_rejects_invented_number(ws):
    from .fakes import responder
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    runner.run_stage(ws, "03_extract", prov)

    def liar(s, u):
        d = json.loads(responder(s, u))
        d["skills"][0]["units"][0]["title"] = "Use a threshold of 4242 tokens"  # the only model-written text
        return json.dumps(d)

    with pytest.raises(runner.StageError, match="not present in extracted units"):
        runner.run_stage(ws, "04_consolidate", FakeProvider(liar))


# ---- AC11
def test_mcp_server_lists_and_serves_skills(ws, tmp_path):
    from mcp.shared.memory import create_connected_server_and_client_session as connect

    from skillsmith.mcp_server import build_server
    run_all(ws)
    dest = tmp_path / "skills"
    workspace.export_skills(ws, dest)
    server = build_server(dest)

    async def go():
        async with connect(server) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            assert {"list_skills", "get_playbook", "get_system_prompt", NAME} <= set(tools)
            assert tools[NAME].description.startswith("Use when")
            # served input schema must agree with tool.json (unit_id enum)
            served = tools[NAME].inputSchema["properties"]["unit_id"]
            tj = json.loads((dest / NAME / "tool.json").read_text())
            enum = tj["input_schema"]["properties"]["unit_id"]["enum"]
            assert all(e in json.dumps(served) for e in enum)
            # matching situation: selects units, says it only selects
            r = await client.call_tool(NAME, {"situation": "retrieval question about a long document archive"})
            text = r.content[0].text
            assert text.startswith("Matched") and "selection only" in text and "Boundaries (where the source says this held" in text
            # non-matching situation: explicit refusal to apply
            r = await client.call_tool(NAME, {"situation": "bake sourdough bread tonight"})
            assert r.content[0].text.startswith("NO MATCH")
            # explicit unit
            r = await client.call_tool(NAME, {"situation": "x", "unit_id": enum[0]})
            assert f"<!-- unit:{enum[0]} -->" in r.content[0].text
            full = await client.call_tool("get_playbook", {"name": NAME})
            assert "Playbook" in full.content[0].text and "p." in full.content[0].text
            bad = await client.call_tool("get_playbook", {"name": "nope"})
            assert bad.isError
            assert (await client.call_tool("get_playbook", {"name": "../x"})).isError
            listed = (await client.list_resources()).resources
            assert [str(r.uri) for r in listed] == [f"skillsmith://{NAME}"]
            res = await client.read_resource(f"skillsmith://{NAME}")
            assert "name: " + NAME in res.contents[0].text

    asyncio.run(go())


# ---- AC12 / AC13 (CLI)
def test_cli_status_router_verify(ws, tmp_path, capsys):
    run_all(ws)
    assert cli.main(["status", str(ws.root)]) == 0
    assert "06_eval: done" in capsys.readouterr().out
    assert cli.main(["router", str(ws.root)]) == 0
    out = capsys.readouterr().out
    assert f"- {NAME}: Use when" in out
    assert cli.main(["verify", str(ws.root)]) == 0
    workspace.export_skills(ws, tmp_path / "s")
    assert cli.main(["router", str(tmp_path / "s")]) == 0
    assert NAME in capsys.readouterr().out


def test_cli_init_and_gate_message(tmp_path, sample_pdf, capsys):
    ws_path = tmp_path / "w"
    assert cli.main(["init", str(ws_path), "--source", str(sample_pdf)]) == 0
    assert cli.main(["run", str(ws_path)]) == 0  # stage 01 needs no provider
    assert cli.main(["approve", str(ws_path), "02_map"]) == 1  # nothing to approve yet
    assert cli.main(["approve", str(ws_path), "03_extract"]) == 1
    assert cli.main(["init", str(ws_path), "--source", str(sample_pdf)]) == 1  # not empty


def test_cli_scanned_exits_2(tmp_path, scanned_pdf, capsys):
    ws_path = tmp_path / "w"
    cli.main(["init", str(ws_path), "--source", str(scanned_pdf)])
    assert cli.main(["run", str(ws_path)]) == 2
    assert "ABSTAIN" in capsys.readouterr().err


def test_verify_cli_exit_code_on_unsourced(ws):
    run_all(ws)
    p = ws.skill_dirs()[0] / "SKILL.md"
    p.write_text(p.read_text().replace("## Failure modes", "- Gain of 61%.\n\n## Failure modes"))
    assert cli.main(["verify", str(ws.root)]) == 1


# ---- AC14
def test_langchain_is_lazy_and_adapter_works_with_duck_model():
    import subprocess
    r = subprocess.run([sys.executable, "-I", "-c",
                        "import sys; sys.path.insert(0, 'src'); import skillsmith.cli, skillsmith.llm;"
                        "assert 'langchain' not in sys.modules and 'langchain_core' not in sys.modules"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    class Msg:
        content = "hello"

    class Model:
        def invoke(self, msgs):
            self.msgs = msgs
            return Msg()

    m = Model()
    assert LangChainProvider(m).complete("sys", "user") == "hello"
    assert len(m.msgs) == 2
    with pytest.raises(RuntimeError):
        get_provider("langchain")
    with pytest.raises(ValueError):
        get_provider("bogus")


def test_package_ships_templates_and_prompts():
    root = workspace.TEMPLATES
    assert (root / "CLAUDE.md").is_file() and (root / "_config" / "prompts" / "stage03_extract.md").is_file()
    for s in workspace.STAGES:
        assert (root / "stages" / s / "CONTEXT.md").is_file()

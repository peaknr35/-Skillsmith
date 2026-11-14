import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from skillsmith import compile as comp, gates, runner, verify, workspace
from skillsmith.ingest import IngestAbstain, ingest_pdf, segment
from skillsmith.ingest.segment import Section, split_long
from skillsmith.llm import FakeProvider
from skillsmith.schema import ActionUnit, EvalSet, SkillSpec, SourceMap

from .fakes import fake, responder

FIX = Path(__file__).parent / "fixtures"


def load_unit(name="unit_valid.json"):
    return json.loads((FIX / name).read_text())


# ---- AC1 / AC2 / AC3
def test_ingest_offset_and_pages(sample_pdf):
    ing = ingest_pdf(sample_pdf)
    assert ing.offset == 2 and ing.page_basis == "printed"
    assert [p.printed_page for p in ing.pages] == [None, None, 1, 2, 3, 4, 5, 6]


def test_scanned_abstains(scanned_pdf):
    with pytest.raises(IngestAbstain, match="scanned"):
        ingest_pdf(scanned_pdf)


def test_segmentation_has_page_ranges(sample_pdf):
    secs = segment(ingest_pdf(sample_pdf))
    titles = [s.title for s in secs]
    assert "2 Method" in titles and "1 Introduction" in titles
    method = next(s for s in secs if s.title == "2 Method")
    assert (method.printed_start, method.printed_end) == (2, 3)  # 2.1 stays inside section 2
    assert "[[printed p. 2 | pdf p. 4]]" in method.text


def test_long_section_splits_with_pages():
    paras = []
    for i in range(1, 7):
        paras += [f"[[printed p. {i} | pdf p. {i + 2}]]", "word " * 400, f"2.{i} Sub heading"]
    sec = Section("ch01", "Big", 3, 8, 1, 6, "\n\n".join(paras))
    parts = split_long(sec, max_tokens=800)
    assert len(parts) > 1
    assert all(p.tokens <= 1000 for p in parts)
    assert parts[0].printed_start == 1 and parts[-1].printed_end == 6
    assert all(p.printed_start is not None for p in parts)


# ---- AC4
def test_schema_accepts_valid_rejects_missing_cite():
    ActionUnit.model_validate(load_unit())
    with pytest.raises(ValidationError):
        ActionUnit.model_validate(load_unit("unit_invalid_no_cite.json"))


def test_schema_description_and_name_rules():
    spec = json.loads((FIX / "skillspec_valid.json").read_text())
    SkillSpec.model_validate(spec)
    for bad in ({"name": "Bad Name"}, {"description": "Use when you want things done quickly please."},
                {"description": "short"}):
        with pytest.raises(ValidationError):
            SkillSpec.model_validate({**spec, **bad})
    with pytest.raises(ValidationError):
        SourceMap.model_validate({"source_type": "method", "actionable": True, "gate_reason": "yes it is",
                                  "chapters": [], "proposed_skills": []})
    with pytest.raises(ValidationError):
        EvalSet.model_validate({"skill": "x", "should_fire": ["a"] * 3, "should_not_fire": ["b"] * 10,
                                "tasks": []})


# ---- AC8 / AC9 / AC10
def _spec():
    return SkillSpec.model_validate(json.loads((FIX / "skillspec_valid.json").read_text()))


def test_compile_outputs_and_tool_schema(tmp_path):
    from jsonschema import Draft202012Validator
    c = comp.compile_spec(_spec())
    d = comp.write_compiled(c, tmp_path)
    for f in ("SKILL.md", "tool.json", "system_prompt.md", "playbook.md", "references/evidence.md"):
        assert (d / f).is_file(), f
    tool = json.loads((d / "tool.json").read_text())
    assert set(tool) == {"name", "description", "input_schema"}
    Draft202012Validator.check_schema(tool["input_schema"])
    assert tool["input_schema"]["required"] == ["situation"]
    assert len((d / "SKILL.md").read_text().splitlines()) <= 500
    assert "p. 2" in (d / "SKILL.md").read_text()


def test_verify_passes_on_compiled_and_flags_unsourced(tmp_path):
    spec = _spec()
    d = comp.write_compiled(comp.compile_spec(spec), tmp_path)
    rep = verify.check_skill_dir(d, spec.units)
    assert rep.checked > 0 and not rep.unsourced, rep.summary()
    md = (d / "SKILL.md").read_text().replace("## Failure modes", "- Expect a 37% gain.\n\n## Failure modes")
    (d / "SKILL.md").write_text(md)
    rep = verify.check_skill_dir(d, spec.units)
    assert [u.number for u in rep.unsourced] == ["37"]


def test_verify_ignores_ids_markers_and_examples():
    text = ("---\nname: x-1\n---\n1. Step with 100 tokens (p. 99).\n- id ch05-u02 and 01_ingest\n"
            "## Worked example\n- costs 777 dollars\n## Next\n- 100\n")
    rep = verify.check_text(text, {"100"})
    assert not rep.unsourced and rep.checked == 2


def _many_units(n, boundaries=0):
    base = _spec().units[0]
    units = []
    for i in range(n):
        u = base.model_copy(deep=True)
        u.id = f"u{i + 1:02d}"
        u.title = f"Apply guidance number {i + 1} for long documents"
        if boundaries:  # unique per unit, so the full render cannot dedupe them
            u.boundaries = [f"Unit {i + 1} holds only under condition {j + 1} of the source." for j in range(boundaries)]
            u.failure_modes = [f"Unit {i + 1} fails when pitfall {j + 1} occurs." for j in range(boundaries)]
        units.append(u)
    return units


def test_compile_uses_lean_mode_when_full_is_too_long_and_loses_nothing():
    spec = _spec()
    spec.units = _many_units(20, boundaries=8)
    assert len(comp.render_skill_md(spec).splitlines()) > 500  # full would have failed before
    c = comp.compile_spec(spec)
    assert c.mode == "lean" and len(c.skill_md.splitlines()) <= 500
    assert "Boundaries and pitfalls: playbook.md, unit u05." in c.skill_md
    # nothing deleted: every unit's boundaries and pitfalls are still in the playbook
    assert all(f"<!-- unit:u{i:02d} -->" in c.playbook_md for i in range(1, 21))
    assert "Unit 7 holds only under condition 8 of the source." in c.playbook_md
    assert "Unit 7 fails when pitfall 8 occurs." in c.playbook_md


def test_compile_falls_back_to_index_mode_for_very_many_units():
    spec = _spec()
    spec.units = _many_units(90, boundaries=8)
    c = comp.compile_spec(spec)
    assert c.mode == "index" and len(c.skill_md.splitlines()) <= 500
    assert all(f"`u{i:02d}`" in c.skill_md for i in range(1, 91))
    assert "## Procedure" not in c.skill_md and "How to use" in c.skill_md


def test_compile_small_skill_stays_full_and_huge_skill_fails_loudly():
    assert comp.compile_spec(_spec()).mode == "full"
    spec = _spec()
    spec.units = _many_units(700)
    with pytest.raises(comp.CompileError, match="even the index-only"):
        comp.compile_spec(spec)


def test_lean_skill_still_passes_verify(tmp_path):
    spec = _spec()
    spec.units = _many_units(20, boundaries=8)
    c = comp.compile_spec(spec)
    d = comp.write_compiled(c, tmp_path)
    assert verify.check_skill_dir(d, spec.units).unsourced == []
    assert "Boundaries and pitfalls" in (d / "SKILL.md").read_text()


# ---- AC7 gates
def test_gate_blocks_until_approved(ws):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    with pytest.raises(gates.GateError):
        runner.run_stage(ws, "03_extract", prov)  # 02 not done
    runner.run_stage(ws, "02_map", prov)
    with pytest.raises(gates.GateError, match="review gate"):
        runner.run_stage(ws, "03_extract", prov)
    gates.approve(ws, "02_map")
    runner.run_stage(ws, "03_extract", prov)
    with pytest.raises(gates.GateError):
        gates.approve(ws, "03_extract")  # not a gate


def test_rerun_of_gate_stage_revokes_approval(ws):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    assert ws.approved("02_map")
    runner.run_stage(ws, "02_map", prov)
    assert not ws.approved("02_map")


# ---- AC5 / AC6
def test_extract_prompts_are_scoped_per_section(ws):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    n_before = len(prov.calls)
    runner.run_stage(ws, "03_extract", prov)
    calls = prov.calls[n_before:]
    secs = json.loads((ws.output("01_ingest") / "sections.json").read_text())
    texts = {s["id"]: (ws.output("01_ingest") / "text" / f"{s['id']}.md").read_text() for s in secs}
    sm = json.loads((ws.output("02_map") / "source_map.json").read_text())
    assert len(calls) == sum(1 for c in sm["chapters"] if c["triage"] != "skip")  # one call per non-skipped section
    for _, user in calls:
        body = user.split("Section text:", 1)[1]
        owners = [i for i, t in texts.items() if t.split("\n\n", 1)[1].strip()[:80] in body]
        assert len(owners) == 1  # exactly one section's text in each prompt


def test_schema_failure_retries_then_fails_without_promotion(ws):
    runner.run_stage(ws, "01_ingest")
    prov = FakeProvider(lambda s, u: "{not json")
    with pytest.raises(runner.StageError, match="3 attempts"):
        runner.run_stage(ws, "02_map", prov)
    assert len(prov.calls) == 3
    assert not ws.done("02_map")
    assert (ws.staging("02_map") / "failed").is_dir()  # failed attempts kept


def test_retry_recovers_after_bad_first_answer(ws):
    runner.run_stage(ws, "01_ingest")
    state = {"n": 0}

    def flaky(s, u):
        state["n"] += 1
        return "oops" if state["n"] == 1 else responder(s, u)

    runner.run_stage(ws, "02_map", FakeProvider(flaky))
    assert ws.done("02_map") and state["n"] == 2


def test_fabricated_number_is_rejected(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    gates.approve(ws, "02_map")

    def liar(s, u):
        out = json.loads(responder(s, u))
        out[0]["defaults"] = [{"parameter": "x", "value": "9999", "cite": out[0]["evidence"][0]["cite"]}]
        return json.dumps(out)

    with pytest.raises(runner.StageError, match="not found in the section text"):
        runner.run_stage(ws, "03_extract", FakeProvider(liar))


def test_non_actionable_source_abstains(ws):
    runner.run_stage(ws, "01_ingest")

    def no(s, u):
        d = json.loads(responder(s, u))
        d["actionable"] = False
        d["proposed_skills"] = []
        d["gate_reason"] = "opinion piece with nothing to do"
        return json.dumps(d)

    runner.run_stage(ws, "02_map", FakeProvider(no))
    gates.approve(ws, "02_map")
    with pytest.raises(runner.StageAbstain, match="not actionable"):
        runner.run_stage(ws, "03_extract", FakeProvider(no))


def test_ingest_abstains_on_scanned(tmp_path, scanned_pdf):
    w = workspace.scaffold(tmp_path / "s", scanned_pdf)
    with pytest.raises(runner.StageAbstain, match="scanned"):
        runner.run_stage(w, "01_ingest")
    assert not w.done("01_ingest") and not [f for f in w.output("01_ingest").iterdir() if f.name != ".gitkeep"]

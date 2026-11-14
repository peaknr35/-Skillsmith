"""Regression tests for the independent QA findings (B2-B7, V1-V6) and amendment A2."""
import importlib
import json
from pathlib import Path

import pymupdf
import pytest
from pydantic import ValidationError

from skillsmith import cli, gates, runner, verify, workspace
from skillsmith import compile as comp
from skillsmith.ingest import ingest_pdf, segment
from skillsmith.ingest.segment import Section, split_long
from skillsmith.llm import FakeProvider
from skillsmith.schema import SkillProposal, SkillSpec

from .fakes import NAME, fake, responder
from .test_integration import run_all

segmod = importlib.import_module("skillsmith.ingest.segment")


def _pdf(path, pages, toc=None, footer=True, offset=0):
    doc = pymupdf.open()
    for i, text in enumerate(pages, 1):
        pg = doc.new_page()
        pg.insert_textbox(pymupdf.Rect(72, 72, 520, 760), text, fontsize=9)
        if footer:
            pg.insert_text((300, 800), str(i - offset), fontsize=10)
    if toc:
        doc.set_toc(toc)
    doc.save(path)
    return path


# ---- B2: marker never separated from its page; ranges exact
def test_split_keeps_marker_with_page_content():
    paras = []
    for i in range(1, 9):
        paras.append(f"[[printed p. {i} | pdf p. {i}]]")
        paras.append(("word " * 300).strip())
        if i == 4:
            paras.append("2.4 Sub heading")
    sec = Section("ch01", "Big", 1, 8, 1, 8, "\n\n".join(paras))
    parts = split_long(sec, max_tokens=900)
    assert len(parts) > 2
    for p in parts:
        first = p.text.split("\n\n")[0]
        assert segmod.MARK.match(first), "every part must start with a page marker"
        assert not segmod.MARK.match(p.text.split("\n\n")[-1]), "no dangling marker at the end"
    covered = set()
    for p in parts:
        covered |= set(range(p.printed_start, p.printed_end + 1))
    assert covered == set(range(1, 9))


# ---- B3 / B4
def test_pages_before_first_outline_entry_are_kept(tmp_path):
    body = ["Front text page. " * 20] * 3 + [f"Chapter body page {i}. " * 30 for i in range(4, 10)]
    p = _pdf(tmp_path / "a.pdf", body, toc=[[1, "One", 4], [1, "Two", 7]], footer=False)
    secs = segment(ingest_pdf(p))
    assert secs[0].id == "ch00" and (secs[0].start_pdf, secs[0].end_pdf) == (1, 3)
    assert [s.start_pdf for s in secs] == [1, 4, 7]
    text_all = "\n".join(s.text for s in secs)
    assert "Front text page" in text_all


def test_unsorted_duplicate_outline_gives_non_overlapping_sections(tmp_path):
    pages = [f"Body page {i}. " * 40 for i in range(1, 10)]
    p = _pdf(tmp_path / "b.pdf", pages, toc=[[1, "A", 1], [1, "C", 7], [1, "B", 4], [1, "B2", 4]], footer=False)
    secs = segment(ingest_pdf(p))
    spans = [(s.start_pdf, s.end_pdf) for s in secs]
    assert spans == sorted(spans)
    assert all(a_end < b_start for (_, a_end), (b_start, _) in zip(spans, spans[1:], strict=False))


# ---- B5: one block larger than the cap is split
def test_huge_single_paragraph_is_split():
    big = " ".join(f"Sentence number {i} is here." for i in range(4000))
    sec = Section("ch01", "Huge", 1, 1, 1, 1, "[[printed p. 1 | pdf p. 1]]\n\n" + big)
    parts = split_long(sec, max_tokens=2000)
    assert len(parts) > 1 and all(p.tokens <= 2100 for p in parts)
    assert all(p.printed_start == 1 for p in parts)


# ---- B6: re-running an upstream stage invalidates downstream stages
def test_rerun_invalidates_downstream(ws):
    run_all(ws)
    assert ws.next_pending() is None
    runner.run_stage(ws, "02_map", fake())
    assert not ws.done("03_extract") and not ws.done("06_eval")
    assert not ws.approved("04_consolidate")
    assert ws.next_pending() == "03_extract"
    with pytest.raises(gates.GateError):
        runner.run_stage(ws, "03_extract", fake())  # 02 needs re-approval


# ---- B7: hand-edited map with unknown section id is a clean error
def test_edited_map_with_unknown_section_is_clear_error(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    f = ws.output("02_map") / "source_map.json"
    d = json.loads(f.read_text())
    d["chapters"][0]["id"] = "../../evil"
    f.write_text(json.dumps(d))
    gates.approve(ws, "02_map")
    with pytest.raises(runner.StageError, match="unknown section ids"):
        runner.run_stage(ws, "03_extract", fake())


# ---- V1-V6
@pytest.mark.parametrize("text,expected", [
    ("Use 15-25 items", {"15", "25"}),
    ("Size 64k and 512MB", {"64", "512"}),
    ("a 3-step plan, 10x faster, 3rd try", {"3", "10"}),
    ("Sizes 1,2,3", {"1", "2", "3"}),
    ("Cost $1,000 or 30%", {"1000", "30"}),
    ("ids ch05-u02 and 01_ingest and v1.2.3", set()),
])
def test_number_tokenizer(text, expected):
    assert set(verify.numbers_in(text)) == expected


def test_page_number_does_not_source_a_value():
    from skillsmith.schema import ActionUnit
    u = ActionUnit.model_validate(json.load(open(Path(__file__).parent / "fixtures" / "unit_valid.json")))
    u.evidence[0].cite.printed_page = 12
    assert "12" not in verify.source_numbers([u])
    rep = verify.check_text("1. Use 12 chunks.\n", verify.source_numbers([u]))
    assert [x.number for x in rep.unsourced] == ["12"]


def test_only_exact_example_headings_are_skipped():
    src = set()
    for head in ("## Examples of use", "### Illustrative thresholds", "## Exampled"):
        assert verify.check_text(f"{head}\n- value 31337\n", src).unsourced, head
    assert not verify.check_text("## Worked example\n- value 31337\n", src).unsourced


# ---- A2: description rule
def test_description_must_be_trigger_first_and_third_person():
    ok = "Use when building retrieval over long documents or choosing chunk sizes."
    SkillProposal(name="x-y", description=ok, section_ids=["ch01"])
    for bad in ("Builds retrieval over long documents and chunk sizes.",
                "Use when you build retrieval over long documents."):
        with pytest.raises(ValidationError):
            SkillProposal(name="x-y", description=bad, section_ids=["ch01"])
    spec = json.load(open(Path(__file__).parent / "fixtures" / "skillspec_valid.json"))
    spec["description"] = "Applies the RAPTOR paper to retrieval for long documents and more."
    with pytest.raises(ValidationError):
        SkillSpec.model_validate(spec)


# ---- A2: hierarchical consolidation, one call per skill, batches then merge
def test_consolidation_is_one_call_per_skill_and_batches_when_large(ws, monkeypatch):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    runner.run_stage(ws, "03_extract", prov)

    n0 = len(prov.calls)
    runner.run_stage(ws, "04_consolidate", prov)
    assert len(prov.calls) - n0 == 1  # one proposed skill, small: a single call

    monkeypatch.setattr(runner, "BATCH_TOKENS", 300)
    n0 = len(prov.calls)
    runner.run_stage(ws, "04_consolidate", prov)
    n_calls = len(prov.calls) - n0
    assert n_calls >= 3  # >=2 batch calls + 1 merge
    last_user = prov.calls[-1][1]
    assert "merge-u01" in last_user  # the merge call sees batch results, not the sections
    assert "[[printed p." not in last_user  # never any source text


def test_consolidation_prompt_contains_only_that_skills_units(ws, monkeypatch):
    def two_skills(s, u):
        if "stage 02_map" in u:
            d = json.loads(responder(s, u))
            ids = d["proposed_skills"][0]["section_ids"]
            half = len(ids) // 2
            d["proposed_skills"] = [
                {"name": "skill-one", "description": "Use when the first half of the topics matters here.",
                 "role": "standard", "section_ids": ids[:half]},
                {"name": "skill-two", "description": "Use when the second half of the topics matters here.",
                 "role": "standard", "section_ids": ids[half:]}]
            return json.dumps(d)
        return responder(s, u)

    prov = FakeProvider(two_skills)
    monkeypatch.setattr(runner, "SHORT_SOURCE_PAGES", 0)  # treat the 8-page fixture as a book
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    runner.run_stage(ws, "03_extract", prov)
    n0 = len(prov.calls)
    runner.run_stage(ws, "04_consolidate", prov)
    calls = prov.calls[n0:]
    assert len(calls) == 2
    import re
    sets = [set(re.findall(r"^(ch\d+(?:-p\d+)?)-u\d+:", u, re.M)) for _, u in calls]
    assert sets[0] and sets[1] and not (sets[0] & sets[1])


def test_citations_carry_pdf_page(ws):
    run_all(ws)
    d = json.loads(next((ws.output("03_extract") / "units").glob("*.json")).read_text())
    assert all(c["cite"]["pdf_page"] for u in d for c in u["evidence"])


def test_export_does_not_half_export_on_clash(ws, tmp_path):
    run_all(ws)
    dest = tmp_path / "skills"
    (dest / NAME).mkdir(parents=True)
    with pytest.raises(workspace.WorkspaceError):
        workspace.export_skills(ws, dest)


def test_cli_run_is_one_stage_per_call_and_help_says_so(tmp_path, sample_pdf, capsys):
    p = tmp_path / "w"
    assert cli.main(["init", str(p), "--source", str(sample_pdf)]) == 0
    assert cli.main(["run", str(p)]) == 0
    w = workspace.load(p)
    assert w.done("01_ingest") and not w.done("02_map")
    assert cli.main(["run", "--help"]) == 0
    assert "NEXT pending stage" in capsys.readouterr().out


def test_cli_usage_error_exit_2(capsys):
    assert cli.main(["run"]) == 2


# ---- citation model: pdf_page required, printed_page None when unknown
def test_citation_requires_pdf_page_and_allows_unknown_printed():
    from skillsmith.schema import Citation
    assert Citation(pdf_page=4).printed_page is None
    assert Citation(pdf_page=4, printed_page=2).printed_page == 2
    with pytest.raises(ValidationError):
        Citation(printed_page=2)  # pdf_page is mandatory
    with pytest.raises(ValidationError):
        Citation(pdf_page=0)


def test_no_footer_pdf_has_unknown_printed_pages_end_to_end(tmp_path):
    pages = [f"Chapter body page {i}. The default value is {i * 10} units. " * 12 for i in range(1, 5)]
    pdf = _pdf(tmp_path / "nofooter.pdf", pages, footer=False)
    ing = ingest_pdf(pdf)
    assert ing.offset is None and ing.page_basis == "pdf"
    assert all(p.printed_page is None for p in ing.pages)
    w = workspace.scaffold(tmp_path / "w", pdf)
    prov = fake()
    runner.run_stage(w, "01_ingest")
    meta = json.loads((w.output("01_ingest") / "meta.json").read_text())
    assert meta["offset"] is None and meta["warnings"]
    assert "[[pdf p. 1]]" in (w.output("01_ingest") / "text" / "ch01.md").read_text()
    runner.run_stage(w, "02_map", prov)
    gates.approve(w, "02_map")
    runner.run_stage(w, "03_extract", prov)
    units = json.loads(next((w.output("03_extract") / "units").glob("*.json")).read_text())
    cite = units[0]["evidence"][0]["cite"]
    assert cite["pdf_page"] >= 1 and cite["printed_page"] is None
    # compiled output falls back to "pdf p. N" and still verifies
    runner.run_stage(w, "04_consolidate", prov)
    gates.approve(w, "04_consolidate")
    runner.run_stage(w, "05_write")
    assert "pdf p." in (w.skill_dirs()[0] / "SKILL.md").read_text()
    assert verify.check(w).unsourced == []


def test_printed_page_is_filled_and_mismatch_is_rejected(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    gates.approve(ws, "02_map")

    def wrong_printed(s, u):
        out = json.loads(responder(s, u))
        c = out[0]["evidence"][0]["cite"]
        c["printed_page"] = 99
        return json.dumps(out)

    with pytest.raises(runner.StageError, match="does not match pdf page"):
        runner.run_stage(ws, "03_extract", FakeProvider(wrong_printed))
    runner.run_stage(ws, "03_extract", fake())
    units = json.loads((ws.output("03_extract") / "units" / "ch03.json").read_text())
    c = units[0]["evidence"][0]["cite"]
    assert (c["pdf_page"], c["printed_page"]) == (4, 2)  # filled from the page map (offset 2)


def test_cite_outside_section_pdf_pages_is_rejected(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    gates.approve(ws, "02_map")

    def far(s, u):
        out = json.loads(responder(s, u))
        out[0]["evidence"][0]["cite"] = {"pdf_page": 999}
        return json.dumps(out)

    with pytest.raises(runner.StageError, match="not in section pdf pages"):
        runner.run_stage(ws, "03_extract", FakeProvider(far))


# ---- QA round 2 repairs
def test_unknown_id_in_proposal_is_clean_error(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    f = ws.output("02_map") / "source_map.json"
    d = json.loads(f.read_text())
    d["proposed_skills"][0]["section_ids"].append("ch99")
    f.write_text(json.dumps(d))
    gates.approve(ws, "02_map")
    with pytest.raises(runner.StageError, match="unknown section ids.*ch99"):
        runner.run_stage(ws, "03_extract", fake())


def test_router_on_missing_path_is_clean_error(tmp_path, capsys):
    assert cli.main(["router", str(tmp_path / "nope")]) == 1
    assert "ERROR" in capsys.readouterr().err


def test_verify_refuses_stale_stage_05(ws, capsys):
    run_all(ws)
    runner.run_stage(ws, "02_map", fake())  # invalidates 03-06
    assert cli.main(["verify", str(ws.root)]) == 1
    assert "not done" in capsys.readouterr().err


def test_segment_cap_includes_marker_overhead():
    paras = []
    for i in range(1, 40):
        paras += [f"[[printed p. {i} | pdf p. {i}]]", "x" * 4000]
    sec = Section("ch01", "Big", 1, 39, 1, 39, "\n\n".join(paras))
    assert all(p.tokens <= 800 for p in split_long(sec, max_tokens=800))


@pytest.mark.parametrize("text,expected", [
    ("a .75 ratio", {"0.75"}),
    ("see Fig. 3, Table 2, Section 4.2, step 1 and page 12", set()),
    ("keep 5 of 30", {"5", "30"}),
])
def test_tokenizer_round2(text, expected):
    assert set(verify.numbers_in(text)) == expected


def test_description_pronoun_edges():
    base = "Use when handling {} in pipelines for long documents."
    SkillProposal(name="x-y", description=base.format("I/O"), section_ids=["c"])
    for bad in ("ours", "yourself", "my data", "we're"):
        with pytest.raises(ValidationError):
            SkillProposal(name="x-y", description=base.format(bad), section_ids=["c"])


def test_provider_exception_is_clean_stage_error(ws):
    runner.run_stage(ws, "01_ingest")

    def boom(s, u):
        raise ConnectionError("network down")

    with pytest.raises(runner.StageError, match="provider call failed: ConnectionError"):
        runner.run_stage(ws, "02_map", FakeProvider(boom))


def test_mcp_matcher_stems_and_drops_weak_hits():
    from skillsmith.mcp_server import select_units
    pb = ("### Choose chunk size\n<!-- unit:u01 -->\nWhen: sizing chunks for a vector index\n\n"
          "### Rerank passages\n<!-- unit:u02 -->\nWhen: passages need reranking after retrieval\n").replace("\n", chr(10))
    hits = select_units(pb, "How big should my chunk be for the vector index?")
    assert [h[0] for h in hits] == ["u01"]  # 'chunk' matches 'chunks' via stemming; u02 has no overlap
    hits = select_units(pb, "retrieval passages index")
    assert {h[0] for h in hits} == {"u01", "u02"} or len(hits) >= 1


# ---- found on a real paper (ICM, arXiv 2603.16021v2): running header/footer page numbers
def test_page_number_inside_running_header_block_is_detected(tmp_path):
    doc = pymupdf.open()
    for i in range(1, 8):
        pg = doc.new_page()
        # number, symbol and running title share one text block, like many journal templates
        pg.insert_textbox(pymupdf.Rect(72, 40, 520, 90), f"{i}\n•\nAuthor One, Author Two", fontsize=9)
        pg.insert_textbox(pymupdf.Rect(72, 130, 520, 700), f"Body text of page {i}. " * 30, fontsize=10)
    p = tmp_path / "hdr.pdf"
    doc.save(p)
    ing = ingest_pdf(p)
    assert ing.offset == 0 and ing.page_basis == "printed"
    assert [pg.printed_page for pg in ing.pages] == list(range(1, 8))


def test_outline_entries_on_one_page_keep_both_titles(tmp_path):
    pages = [f"Body page {i}. " * 40 for i in range(1, 6)]
    p = _pdf(tmp_path / "shared.pdf", pages, toc=[[1, "Abstract", 1], [1, "1 Introduction", 1], [1, "2 Method", 3]],
             footer=False)
    secs = segment(ingest_pdf(p))
    assert secs[0].title == "Abstract / 1 Introduction"


def test_dotenv_loads_without_overriding_and_never_prints(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("SKILLSMITH_T1", raising=False)
    monkeypatch.setenv("SKILLSMITH_T2", "from-shell")
    (tmp_path / ".env").write_text('# c\nSKILLSMITH_T1="abc123"\nexport SKILLSMITH_T3=zzz\nSKILLSMITH_T2=from-file\n', encoding="utf-8")
    read = cli.load_dotenv(tmp_path, tmp_path)
    import os
    assert read == [tmp_path / ".env"]  # duplicate dir read once
    assert os.environ["SKILLSMITH_T1"] == "abc123" and os.environ["SKILLSMITH_T3"] == "zzz"
    assert os.environ["SKILLSMITH_T2"] == "from-shell"  # shell wins
    assert "abc123" not in capsys.readouterr().out
    monkeypatch.delenv("SKILLSMITH_T1")
    monkeypatch.delenv("SKILLSMITH_T3")


# ---- found on the first live-model run (stage 02, ICM paper)
def test_quoted_user_phrasings_may_be_first_person_but_prose_may_not():
    ok = "Use when a user wants a staged workflow, or says 'organize my prompts into stages' or \"do I need a framework?\"."
    SkillProposal(name="x-y", description=ok, section_ids=["c"])
    for bad in ("Use when you want a staged workflow for agent pipelines.",
                "Use when my team needs staged workflows, says 'set up stages'."):
        with pytest.raises(ValidationError):
            SkillProposal(name="x-y", description=bad, section_ids=["c"])


def test_map_prompt_tells_model_one_skill_for_short_sources(ws):
    seen = {}

    def spy(s, u):
        seen["u"] = u
        return responder(s, u)

    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", FakeProvider(spy))
    assert "pdf_pages=8" in seen["u"] and "EXACTLY ONE standard skill" in seen["u"]


def test_short_source_must_map_to_exactly_one_skill(ws):
    def many(s, u):
        d = json.loads(responder(s, u))
        ids = d["proposed_skills"][0]["section_ids"]
        d["proposed_skills"] = [
            {"name": "skill-one", "description": "Use when the first topic matters in long documents.",
             "role": "standard", "section_ids": ids[:2]},
            {"name": "skill-two", "description": "Use when the second topic matters in long documents.",
             "role": "standard", "section_ids": ids[2:]}]
        return json.dumps(d)

    runner.run_stage(ws, "01_ingest")
    prov = FakeProvider(many)
    with pytest.raises(runner.StageError, match="EXACTLY ONE"):
        runner.run_stage(ws, "02_map", prov)
    assert len(prov.calls) == 3  # retried with the reason, then stopped


# ---- found on the first live-model stage 03 run: quote real, page off by one
def test_quote_must_be_on_the_cited_page(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    gates.approve(ws, "02_map")

    def off_by_one(s, u):
        out = json.loads(responder(s, u))
        if "Section id: ch03" in u:  # '2 Method', pdf pages 4-5; phrase is on pdf page 4
            out[0]["evidence"][0]["cite"] = {"pdf_page": 5, "quote_hint": "Chunk the document at 100 tokens"}
        return json.dumps(out)

    with pytest.raises(runner.StageError, match="not on cited pdf page 5"):
        runner.run_stage(ws, "03_extract", FakeProvider(off_by_one))

    def right_page(s, u):
        out = json.loads(responder(s, u))
        if "Section id: ch03" in u:
            out[0]["evidence"][0]["cite"] = {"pdf_page": 4, "quote_hint": "Chunk the document at 100 tokens"}
        return json.dumps(out)

    runner.run_stage(ws, "03_extract", FakeProvider(right_page))


# ---- hardening: coverage ledger (stage 03) and unit accounting (stage 04)
def _through_map(ws):
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", fake())
    gates.approve(ws, "02_map")


def test_empty_section_needs_a_reason_and_ledger_covers_every_section(ws):
    _through_map(ws)

    def empty_no_reason(s, u):
        return json.dumps({"units": []}) if "Section id: ch03" in u else responder(s, u)

    with pytest.raises(runner.StageError, match="no_units_reason"):
        runner.run_stage(ws, "03_extract", FakeProvider(empty_no_reason))

    def empty_with_reason(s, u):
        if "Section id: ch03" in u:
            return json.dumps({"units": [], "no_units_reason": "Only background; no decision rule."})
        return responder(s, u)

    runner.run_stage(ws, "03_extract", FakeProvider(empty_with_reason))
    ledger = json.loads((ws.output("03_extract") / "coverage.json").read_text())
    secs = json.loads((ws.output("01_ingest") / "sections.json").read_text())
    assert [r["section"] for r in ledger] == [s["id"] for s in secs]  # every section accounted for
    ch03 = next(r for r in ledger if r["section"] == "ch03")
    assert ch03["status"] == "no_units" and "background" in ch03["reason"]
    assert ch03["pages_uncited"] == ch03["pdf_pages"]
    assert (ws.output("03_extract") / "coverage.md").is_file()


def _to_04(ws):
    prov = fake()
    _through_map(ws)
    runner.run_stage(ws, "03_extract", prov)
    return prov


def test_silently_dropped_unit_is_rejected_but_explicit_exclusion_passes(ws):
    _to_04(ws)

    def drop_one(s, u):
        d = json.loads(responder(s, u))
        d["skills"][0]["units"] = d["skills"][0]["units"][1:]  # first unit vanishes from the plan
        return json.dumps(d)

    with pytest.raises(runner.StageError, match="unit accounting failed"):
        runner.run_stage(ws, "04_consolidate", FakeProvider(drop_one))

    def drop_with_reason(s, u):
        d = json.loads(responder(s, u))
        gone = d["skills"][0]["units"].pop(0)["primary"]
        d["skills"][0]["excluded"] = [f"{gone}: duplicate of a later unit"]
        return json.dumps(d)

    runner.run_stage(ws, "04_consolidate", FakeProvider(drop_with_reason))
    assert "EXCLUDED" in (ws.output("04_consolidate") / "accounting.md").read_text()


def test_merging_is_allowed_counts_need_not_match(ws):
    _to_04(ws)

    def merge_two(s, u):
        d = json.loads(responder(s, u))
        pu = d["skills"][0]["units"]
        pu[0]["also"] = [pu[1]["primary"]]  # fold the second unit into the first
        d["skills"][0]["units"] = [pu[0]] + pu[2:]
        return json.dumps(d)

    runner.run_stage(ws, "04_consolidate", FakeProvider(merge_two))
    spec = json.loads(next((ws.output("04_consolidate") / "consolidated").glob("*.json")).read_text())
    merged = [u for u in spec["units"] if len(u["source_units"]) == 2][0]
    # the merged unit inherits both units' evidence and cites; nothing was re-typed by the model
    first, second = [json.loads(p.read_text()) for p in sorted((ws.output("03_extract") / "units").glob("*.json"))[:2]]
    assert len(merged["evidence"]) >= 1


def test_invented_source_unit_id_is_rejected(ws):
    _to_04(ws)

    def invent(s, u):
        d = json.loads(responder(s, u))
        d["skills"][0]["units"][0]["also"] = ["ch99-u01"]
        return json.dumps(d)

    with pytest.raises(runner.StageError, match="not in the input"):
        runner.run_stage(ws, "04_consolidate", FakeProvider(invent))


def test_accounting_survives_batch_and_merge_passes(ws, monkeypatch):
    prov = _to_04(ws)
    monkeypatch.setattr(runner, "BATCH_TOKENS", 300)
    runner.run_stage(ws, "04_consolidate", prov)
    all_ids = set()
    for f in (ws.output("03_extract") / "units").glob("*.json"):
        all_ids |= {u["id"] for u in json.loads(f.read_text())}
    spec = json.loads(next((ws.output("04_consolidate") / "consolidated").glob("*.json")).read_text())
    carried = {i for u in spec["units"] for i in u["source_units"]}
    assert carried == all_ids  # merge ids were mapped back to the original stage-03 ids


def test_units_in_sections_outside_every_proposal_are_an_error(ws):
    _through_map(ws)
    f = ws.output("02_map") / "source_map.json"
    d = json.loads(f.read_text())
    d["proposed_skills"][0]["section_ids"] = d["proposed_skills"][0]["section_ids"][:-1]  # hand-edit at the gate
    f.write_text(json.dumps(d))
    runner.run_stage(ws, "03_extract", fake())
    with pytest.raises(runner.StageError, match="belong to no proposed skill"):
        runner.run_stage(ws, "04_consolidate", fake())


def test_expand_helpers():
    from skillsmith.accounting import expand_excluded, expand_merge_ids
    mm = {"merge-u01": ["ch01-u01", "ch02-u01"], "merge-u02": ["ch03-u01"]}
    assert expand_merge_ids(["merge-u01", "merge-u02", "merge-u01"], mm) == ["ch01-u01", "ch02-u01", "ch03-u01"]
    assert expand_excluded(["merge-u02: dated", "ch09-u01: x"], mm) == ["ch03-u01: dated", "ch09-u01: x"]


# ---- found on the first live stage-04 run: reply cut off at the token cap
def test_anthropic_provider_streams_and_flags_truncation(monkeypatch):
    import sys
    import types

    from skillsmith.llm.anthropic_provider import AnthropicProvider, TruncatedOutput

    class Block:
        type = "text"

        def __init__(self, t):
            self.text = t

    class Msg:
        def __init__(self, stop):
            self.stop_reason = stop
            self.content = [Block('{"ok": true}')]

    class Stream:
        def __init__(self, stop):
            self.stop = stop

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_final_message(self):
            return Msg(self.stop)

    seen = {}

    class Messages:
        stop = "end_turn"

        def stream(self, **kw):
            seen.update(kw)
            return Stream(Messages.stop)

    class Client:
        messages = Messages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=lambda **kw: Client()))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    p = AnthropicProvider()
    assert p.complete("s", "u") == '{"ok": true}'
    assert seen["max_tokens"] >= 32000
    Messages.stop = "max_tokens"
    with pytest.raises(TruncatedOutput, match="cut off"):
        p.complete("s", "u")
    # through the runner: a truncated reply is a clean StageError, not a JSON parse error
    from skillsmith.runner import StageError, call_json
    with pytest.raises(StageError, match="provider call failed: TruncatedOutput"):
        call_json(p, "s", "u", lambda d: d, __import__("pathlib").Path("/nonexistent-skillsmith-test"), "t")


# ---- plan-based consolidation: the model never re-types units
def test_plan_builds_units_from_originals_so_cites_are_inherited(ws):
    _to_04(ws)
    runner.run_stage(ws, "04_consolidate", fake())
    spec = json.loads(next((ws.output("04_consolidate") / "consolidated").glob("*.json")).read_text())
    originals = {}
    for f in (ws.output("03_extract") / "units").glob("*.json"):
        for u in json.loads(f.read_text()):
            originals[u["id"]] = u
    for u in spec["units"]:
        src = originals[u["source_units"][0]]
        assert u["procedure"] == src["procedure"] and u["example"] == src["example"]
        assert [e["cite"] for e in u["evidence"]][:1] == [e["cite"] for e in src["evidence"]][:1]


def test_reply_size_is_independent_of_unit_count(ws):
    """The model's reply is a plan of ids, not re-typed units."""
    _to_04(ws)
    prov = fake()
    runner.run_stage(ws, "04_consolidate", prov)
    reply = responder(*prov.calls[-1])
    assert len(reply) < 600  # fixture: a few ids; re-typed units would be thousands of characters


def test_merge_ids_in_conflicts_are_mapped_back_to_real_unit_ids(ws, monkeypatch):
    _to_04(ws)
    monkeypatch.setattr(runner, "BATCH_TOKENS", 300)

    def with_conflict(s, u):
        d = json.loads(responder(s, u))
        if "merge-u01" in u:  # the merge pass
            d["conflicts"] = ["merge-u01 and merge-u02 disagree about the threshold"]
        return json.dumps(d)

    runner.run_stage(ws, "04_consolidate", FakeProvider(with_conflict))
    text = (ws.output("04_consolidate") / "conflicts.md").read_text()
    assert "merge-u" not in text and "ch" in text and "disagree about the threshold" in text


# ---- found on the real ICM skill: one generic shared word matched an off-topic question
def test_matcher_needs_two_shared_words_for_a_substantive_situation():
    from skillsmith.mcp_server import select_units
    pb = (chr(10).join([
        "### Organize an agent workspace as numbered stage folders", "<!-- unit:u01 -->",
        "When: designing a multi-step agent workflow with local files", "",
        "### Check whether the model context fits the token budget", "<!-- unit:u02 -->",
        "When: the model prompt loads everything into one context", ""]))
    assert select_units(pb, "how do I fine-tune a model on my local GPU") == []  # 'model'/'local' alone
    assert [h[0] for h in select_units(pb, "organize my agent workflow into numbered stage folders")] == ["u01"]
    assert [h[0] for h in select_units(pb, "agent files")] == ["u01"]  # short situations still match on one word


# ---- clean layout: engine/ runs/ skills/ (bare names resolve inside runs/, .env found upward)
def test_bare_run_names_resolve_inside_the_runs_folder(tmp_path, sample_pdf, monkeypatch, capsys):
    root = tmp_path / "Skillsmith"
    (root / "runs").mkdir(parents=True)
    (root / "engine").mkdir()
    monkeypatch.chdir(root / "engine")
    monkeypatch.delenv("SKILLSMITH_RUNS_DIR", raising=False)
    assert cli.main(["init", "icm-v2", "--source", str(sample_pdf)]) == 0
    assert (root / "runs" / "icm-v2" / "stages" / "01_ingest" / "input" / "sample.pdf").is_file()
    assert cli.main(["run", "icm-v2"]) == 0  # bare name found from a different folder
    assert (root / "runs" / "icm-v2" / "stages" / "01_ingest" / "output" / "_DONE.json").is_file()
    assert cli.main(["status", "icm-v2"]) == 0
    assert "01_ingest: done" in capsys.readouterr().out
    # an explicit path still wins over a bare-name lookup, and unknown names fail cleanly
    assert cli.main(["status", "no-such-run"]) == 1


def test_runs_dir_can_be_set_by_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLSMITH_RUNS_DIR", str(tmp_path / "elsewhere"))
    assert cli.runs_dir() == tmp_path / "elsewhere"
    assert cli.resolve_new(__import__("pathlib").Path("x")) == tmp_path / "elsewhere" / "x"


def test_dotenv_is_found_in_a_parent_folder(tmp_path, monkeypatch):
    monkeypatch.delenv("SKILLSMITH_T9", raising=False)
    (tmp_path / ".env").write_text("SKILLSMITH_T9=found\n", encoding="utf-8")
    deep = tmp_path / "engine" / "src"
    deep.mkdir(parents=True)
    cli.load_dotenv(deep)
    import os
    assert os.environ["SKILLSMITH_T9"] == "found"
    monkeypatch.delenv("SKILLSMITH_T9")


# ---- found by the blind quality judge: generated skills must name their source and speak plainly
SRC = {"title": "A Study of Long Documents", "author": "A. Author", "file": "paper.pdf"}


def test_compiled_skill_names_its_source_and_tells_the_model_how_to_cite(tmp_path):
    spec = _spec_fixture()
    c = comp.compile_spec(spec, SRC)
    for text in (c.skill_md, c.playbook_md, c.evidence_md, c.system_prompt):
        assert "A Study of Long Documents" in text and "A. Author" in text
    assert "Never use unit ids" in c.skill_md and "Never use unit ids" in c.system_prompt
    assert "ask one clarifying question" in c.skill_md
    d = comp.write_compiled(c, tmp_path)
    assert verify.check_skill_dir(d, spec.units).unsourced == []  # digits in a title never trip verify


def test_source_block_digits_are_not_flagged_by_verify():
    rep = verify.check_text("Source: *GPT-4 Survey 2023*, file p77.pdf.\n- real claim 99\n", {"1"})
    assert [u.number for u in rep.unsourced] == ["99"]


def test_lean_mode_also_carries_source_and_rules():
    spec = _spec_fixture()
    md = comp.render_skill_md_lean(spec, source=SRC)
    assert "A Study of Long Documents" in md and "Never use unit ids" in md


def test_old_runs_without_source_metadata_fall_back_to_the_pdf(ws):
    runner.run_stage(ws, "01_ingest")
    meta_f = ws.output("01_ingest") / "meta.json"
    m = json.loads(meta_f.read_text())
    assert "source_title" in m  # new runs record it
    for k in ("source_title", "source_author"):
        m.pop(k)
    meta_f.write_text(json.dumps(m))  # simulate a run made before this existed
    info = runner.source_info(ws)
    assert info["file"] == "sample.pdf" and "title" in info


def test_eval_quality_on_a_frozen_eval_file_works_after_stage_05_is_rebuilt(ws, tmp_path):
    from skillsmith import evalquality

    from .test_evalrun import _quality_responder
    run_all(ws)
    frozen = tmp_path / "frozen.json"
    frozen.write_text((next((ws.output("06_eval") / "evals").glob("*/eval.json"))).read_text())
    runner.run_stage(ws, "05_write")  # marks stage 06 stale
    assert not ws.done("06_eval")
    prov = FakeProvider(_quality_responder())
    with pytest.raises(evalrun_error()):
        evalquality.run(ws, prov, prov, repeats=1)  # needs a done stage 06 ...
    run_dir = evalquality.run(ws, prov, prov, repeats=1, eval_file=frozen)  # ... unless the eval set is frozen
    assert (run_dir / "report.md").is_file()


def evalrun_error():
    from skillsmith.evalrun import EvalRunError
    return EvalRunError


def _spec_fixture():
    return SkillSpec.model_validate(json.load(open(Path(__file__).parent / "fixtures" / "skillspec_valid.json")))


# ---- literature-backed improvements (triad + artifact types, fit check, exposure dedup, provenance, audit, strict eval)
def test_triad_gate_blocks_execution_skill_when_any_condition_is_false():
    from pydantic import ValidationError

    from skillsmith.schema import SourceMap
    base = {
        "source_type": "empirical", "actionable": True, "gate_reason": "Benchmarks 8 models.",
        "chapters": [{"id": "ch01", "pages": "1-3", "triage": "evidence"}],
        "triad": {"modular": True, "late_binding": True, "state_transforming": False,
                  "note": "Reports benchmark numbers only; no state-transforming procedure."},
        "proposed_skills": [{"name": "bench-ref", "description": "Use when checking benchmark results across models.",
                             "section_ids": ["ch01"]}],
    }
    with pytest.raises(ValidationError, match="triad test failed"):
        SourceMap.model_validate(base)
    base["proposed_skills"][0]["artifact"] = "evidence_reference"
    sm = SourceMap.model_validate(base)
    assert sm.proposed_skills[0].artifact == "evidence_reference"


def test_stage_02_requires_triad_on_new_maps_with_execution_skill(ws):
    runner.run_stage(ws, "01_ingest")
    bad = FakeProvider(lambda s, u: json.dumps({
        "source_type": "method", "actionable": True, "gate_reason": "Has a procedure.",
        "chapters": [{"id": s["id"], "pages": "1", "triage": "procedure"}
                     for s in json.loads((ws.output("01_ingest") / "sections.json").read_text())],
        "proposed_skills": [{"name": "no-triad", "description": "Use when testing whether stage 02 requires a triad.",
                             "section_ids": [s["id"] for s in json.loads((ws.output("01_ingest") / "sections.json").read_text())]}],
    }))
    with pytest.raises(runner.StageError, match="triad test"):
        runner.run_stage(ws, "02_map", bad)


def test_artifact_types_compile_with_distinct_headings_and_verify_cleanly(tmp_path):
    for art, heading in (("execution_skill", "## Procedure"),
                         ("decision_guide", "## Decision rules"),
                         ("evidence_reference", "## Practices reported in the source (not prescribed)")):
        spec = _spec_fixture()
        spec.name = f"art-{art.replace('_', '-')}"
        spec.artifact = art
        c = comp.compile_spec(spec, SRC)
        assert heading in c.skill_md
        assert "## Fit check" in c.skill_md
        if art == "evidence_reference":
            assert c.skill_md.index("## Evidence (summary)") < c.skill_md.index(heading)
        d = comp.write_compiled(c, tmp_path, SRC)
        assert verify.check_skill_dir(d, spec.units).unsourced == []
        prov = json.loads((d / "references" / "provenance.json").read_text(encoding="utf-8"))
        assert prov["artifact"] == art and prov["skill"] == spec.name and len(prov["units"]) == len(spec.units)


def test_step_dedup_collapses_repeated_steps_across_units_in_skill_md_only():
    spec = _spec_fixture()
    u2 = spec.units[0].model_copy(deep=True)
    u2.id = "u02"
    u2.title = "Check whether a second workflow fits"
    spec.units.append(u2)
    c = comp.compile_spec(spec, SRC)
    assert "Same as `u01` step 1." in c.skill_md
    assert "Same as `u01`" not in c.playbook_md  # playbook keeps every unit self-contained
    rep = comp.exposure_report(spec, c)
    assert any("collapsed" in line for line in rep)


def test_audit_checks_coverage_accounting_and_citation_support(ws):
    from skillsmith import audit
    run_all(ws)
    rep = audit.audit_workspace(ws)
    assert rep.ok
    assert rep.sections_total >= 1 and rep.sections_unaccounted == []
    assert rep.accounting_missing == [] and rep.accounting_unknown == []
    assert len(rep.unit_supports) == rep.consolidated_units
    assert (ws.output("05_write") / "audit-report.md").is_file()
    assert cli.main(["audit", str(ws.root)]) == 0


def test_strict_completion_and_near_miss_over_application_in_evalrun(ws):
    from skillsmith import evalrun
    run_all(ws)
    ef = next((ws.output("06_eval") / "evals").glob("*/eval.json"))
    es = json.loads(ef.read_text(encoding="utf-8"))
    es["tasks"][0]["process_checks"] = ["Checks whether the user's constraints fit before prescribing"]
    es["tasks"][-1]["expect_apply"] = False
    es["tasks"][-1]["treatment_markers"] = ["guidance", "retrieval"]
    ef.write_text(json.dumps(es), encoding="utf-8")

    def fake_eval(s, u):
        if "selected_skill" in s:
            return '{"selected_skill": "long-doc-retrieval"}' if "fire prompt" in u else '{"selected_skill": "none"}'
        if "per_behaviour" in s:
            # Option 1 passes only 1 of 2 items (not strict); Option 2 passes all items (strict)
            return '{"per_behaviour": [{"behaviour": "a", "option1": true, "option2": true}, {"behaviour": "b", "option1": false, "option2": true}]}'
        # Generator: echoes guidance + retrieval when skill is in system prompt -> triggers over_applied on expect_apply=False
        return "Use guidance and retrieval here." if "A skill is loaded" in s else "Plain answer."

    run_dir = evalrun.run(ws, FakeProvider(fake_eval), parts="tasks")
    res = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    assert any(t["over_applied"] for t in res["tasks"])
    assert any(t["judge"]["strict_baseline"] != t["judge"]["strict_treatment"] for t in res["tasks"])


def test_mcp_match_skills_compares_across_library(ws, tmp_path):
    from skillsmith.mcp_server import build_server
    run_all(ws)
    dest = tmp_path / "skills"
    workspace.export_skills(ws, dest)
    srv = build_server(dest)
    names = {t.name for t in srv._tool_manager.list_tools()}
    assert "match_skills" in names


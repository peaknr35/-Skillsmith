"""Stage runner. Builds scoped prompts from the stage contract, calls the provider,
validates output against schemas, writes to staging, then promotes."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from . import verify as verify_mod
from .accounting import account, expand_excluded, expand_merge_ids
from .consolidate import ConsolidationPlan, PlanError, to_result
from .compile import CompileError, compile_spec, exposure_report, write_compiled
from .evals import write_evals
from .gates import GateError, require_prereqs
from .ingest import IngestAbstain, ingest_pdf, segment
from .schema import (ActionUnit, ChapterTriage, ConsolidationResult, EvalSet, SourceMap)
from .workspace import STAGES, Workspace

RETRIES = 2
CUE_FILLER = {"with", "from", "that", "this", "than", "then", "when", "each", "only", "plain", "into", "over", "their", "they", "have", "such", "more", "most", "very", "shaped"}
# everyday words that can never count as a method's signature vocabulary (neutral tasks may use them)
GENERIC_CUES = {"workflow", "workflows", "pipeline", "pipelines", "process", "processes", "step", "steps", "agent",
                "agents", "ai", "context", "model", "models", "review", "output", "outputs", "input", "inputs", "tool",
                "tools", "prompt", "prompts", "task", "tasks", "system", "data", "file", "files", "document", "report"}
SHORT_SOURCE_PAGES = 30  # at or below this many PDF pages a source maps to exactly one skill

STAGE_CONFIG = {
    "02_map": ["extraction-guide.md", "skill-template.md"],
    "03_extract": ["extraction-guide.md", "ethics-filter.md"],
    "04_consolidate": ["extraction-guide.md", "ethics-filter.md", "quality-checklist.md"],
    "06_eval": ["quality-checklist.md", "skill-template.md"],
}


class StageError(Exception):
    """Stage failed after bounded retries. Staging dir is kept for diagnosis."""


class StageAbstain(Exception):
    """Stage lacks the input or evidence it needs and says why."""


class CheckError(ValueError):
    """Deterministic check on model output failed (triggers a retry)."""


# ---------------------------------------------------------------- helpers
def extract_json(raw: str):
    s = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
    if fence:
        s = fence.group(1).strip()
    starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON found in the answer")
    start = min(starts)
    end = max(s.rfind("}"), s.rfind("]"))
    if end < start:
        raise ValueError("unterminated JSON")
    return json.loads(s[start:end + 1])


def call_json(provider, system: str, user: str, parse: Callable, fail_dir: Path, tag: str):
    prompt, err = user, None
    for attempt in range(RETRIES + 1):
        try:
            raw = provider.complete(system, prompt)
        except Exception as e:  # provider/network/SDK failure: not a parse problem, do not retry blindly
            raise StageError(f"{tag}: provider call failed: {type(e).__name__}: {e}") from e
        try:
            return parse(extract_json(raw))
        except (ValueError, ValidationError, CheckError) as e:
            err = e
            fail_dir.mkdir(parents=True, exist_ok=True)
            (fail_dir / f"{tag}.attempt{attempt}.txt").write_text(raw, encoding="utf-8")
            prompt = (user + f"\n\nYour previous answer was rejected:\n{e}\n"
                      "Return corrected JSON only, no commentary.")
    raise StageError(f"{tag}: output rejected after {RETRIES + 1} attempts: {str(err)[:600]}")


def render(template: str, **kw) -> str:
    for k, v in kw.items():
        template = template.replace("{{" + k + "}}", str(v))
    return template


def system_prompt(w: Workspace, stage: str) -> str:
    parts = [(w.root / "CLAUDE.md").read_text(encoding="utf-8")]
    for name in STAGE_CONFIG.get(stage, []):
        parts.append(f"## _config/{name}\n" + w.config(name))
    parts.append(f"## stages/{stage}/CONTEXT.md\n" + (w.stage_dir(stage) / "CONTEXT.md").read_text(encoding="utf-8"))
    parts.append("Output must be valid JSON only. Never invent numbers or pages.")
    return "\n\n".join(parts)


def prompt_template(w: Workspace, name: str) -> str:
    return w.config(f"prompts/{name}")


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _promote(w: Workspace, stage: str) -> Path:
    """Swap staging into output with rollback, then invalidate everything downstream."""
    stg, out = w.staging(stage), w.output(stage)
    old = out.with_name("output.old")
    if old.exists():
        shutil.rmtree(old)
    if out.exists():
        out.rename(old)  # a re-run also invalidates this stage's previous APPROVED
    try:
        stg.rename(out)
    except OSError:
        if old.exists():
            old.rename(out)
        raise
    if old.exists():
        shutil.rmtree(old, ignore_errors=True)
    (out / "_DONE.json").write_text(json.dumps(
        {"stage": stage, "at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    for later in STAGES[STAGES.index(stage) + 1:]:  # stale: outputs were built from the old version
        for marker in ("_DONE.json", "APPROVED"):
            f = w.output(later) / marker
            if f.exists():
                f.unlink()
    return out


def _fresh_staging(w: Workspace, stage: str) -> Path:
    stg = w.staging(stage)
    if stg.exists():
        shutil.rmtree(stg)
    stg.mkdir(parents=True)
    return stg


def _units_md(units: list[ActionUnit], title: str) -> str:
    from .compile import _unit_block
    L = [f"# {title}", ""]
    for u in units:
        L += _unit_block(u, playbook=True)
        L.append(f"Evidence grades: {', '.join(e.grade.value for e in u.evidence)}")
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- stage 01
def stage_ingest(w: Workspace) -> Path:
    pdfs = sorted(w.input("01_ingest").glob("*.pdf"))
    if not pdfs:
        raise StageAbstain("no PDF in stages/01_ingest/input/")
    if len(pdfs) > 1:
        raise StageAbstain("more than one PDF in input/; one source per workspace")
    try:
        ing = ingest_pdf(pdfs[0])
    except IngestAbstain as e:
        raise StageAbstain(str(e)) from e
    secs = segment(ing)
    by_pdf = {p.pdf_page: p for p in ing.pages}
    stg = _fresh_staging(w, "01_ingest")
    (stg / "text").mkdir()
    meta = {"source": pdfs[0].name, "pdf_pages": len(ing.pages), "offset": ing.offset,
            "page_basis": ing.page_basis, "warnings": ing.warnings,
            "source_title": ing.title, "source_author": ing.author}
    (stg / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (stg / "pages.jsonl").open("w", encoding="utf-8") as f:
        for p in ing.pages:
            f.write(json.dumps({"pdf_page": p.pdf_page, "printed_page": p.printed_page,
                                "label": p.label, "blocks": p.blocks}) + "\n")
    rows = ["# page-map", "", f"offset (pdf - printed): {ing.offset}  basis: {ing.page_basis}", "",
            "| pdf | printed | label |", "|---|---|---|"]
    rows += [f"| {p.pdf_page} | {p.printed_page if p.printed_page is not None else '-'} | {p.label or '-'} |"
             for p in ing.pages]
    (stg / "page-map.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    sec_meta = []
    for s in secs:
        (stg / "text" / f"{s.id}.md").write_text(f"# {s.title}\n\n{s.text}\n", encoding="utf-8")
        sec_meta.append({"id": s.id, "title": s.title, "start_pdf": s.start_pdf, "end_pdf": s.end_pdf,
                         "printed_start": s.printed_start, "printed_end": s.printed_end,
                         "tokens": s.tokens, "pdf_pages": s.pdf_pages()})
    (stg / "sections.json").write_text(json.dumps(sec_meta, indent=2), encoding="utf-8")
    toc = ["# toc", ""] + [f"- {m['id']}: {m['title']} (pdf {m['start_pdf']}-{m['end_pdf']}, printed {m['printed_start'] if m['printed_start'] else 'unknown'}-{m['printed_end'] if m['printed_end'] else 'unknown'}, "
                           f"~{m['tokens']} tokens)" for m in sec_meta]
    (stg / "toc.md").write_text("\n".join(toc) + "\n", encoding="utf-8")
    if not sec_meta:
        raise StageError("segmentation produced no sections")
    return _promote(w, "01_ingest")


# ---------------------------------------------------------------- stage 02
def _sections(w: Workspace) -> list[dict]:
    return json.loads((w.output("01_ingest") / "sections.json").read_text(encoding="utf-8"))


def _preview(text: str, n: int = 260) -> str:
    t = re.sub(r"\[\[[^\]]*\]\]", " ", text)
    return " ".join(t.split())[:n]


def stage_map(w: Workspace, provider) -> Path:
    secs = _sections(w)
    meta = json.loads((w.output("01_ingest") / "meta.json").read_text(encoding="utf-8"))
    ids = {s["id"] for s in secs}
    table = "\n".join(
        f"{s['id']} | {s['title']} [printed {s['printed_start'] or 'unknown'}-{s['printed_end'] or 'unknown'}] | "
        f"{s['start_pdf']}-{s['end_pdf']} | {s['tokens']} | "
        f"{_preview((w.output('01_ingest') / 'text' / (s['id'] + '.md')).read_text(encoding='utf-8'))}"
        for s in secs)
    user = render(prompt_template(w, "stage02_map.md"),
                  PAGE_INFO=f"pdf_pages={meta['pdf_pages']} offset={meta['offset']} basis={meta['page_basis']}",
                  SECTION_TABLE=table, SCHEMA=json.dumps(SourceMap.model_json_schema()))
    stg = _fresh_staging(w, "02_map")

    def parse(data) -> SourceMap:
        sm = SourceMap.model_validate(data)
        got = {c.id for c in sm.chapters}
        if got != ids:
            raise CheckError(f"chapters must list exactly the section ids; missing={sorted(ids - got)} "
                             f"unknown={sorted(got - ids)}")
        if sm.actionable and meta["pdf_pages"] <= SHORT_SOURCE_PAGES and len(sm.proposed_skills) != 1:
            raise CheckError(
                f"this source has {meta['pdf_pages']} PDF pages (<= {SHORT_SOURCE_PAGES}): propose EXACTLY ONE "
                f"standard skill covering every non-skip section, not {len(sm.proposed_skills)}. "
                "No router and no sub-skills; several skills from a short paper compete for triggers.")
        if sm.actionable:
            if any(p.artifact == "execution_skill" for p in sm.proposed_skills) and sm.triad is None:
                raise CheckError("an execution_skill proposal needs the triad test: \"triad\": {\"modular\": bool, "
                                 "\"late_binding\": bool, \"state_transforming\": bool, \"note\": \"...\"}. If any is "
                                 "false, use artifact decision_guide or evidence_reference, or set actionable=false")
            assigned = {i for p in sm.proposed_skills for i in p.section_ids}
            unknown = assigned - ids
            if unknown:
                raise CheckError(f"proposals reference unknown section ids {sorted(unknown)}")
            need = {c.id for c in sm.chapters if c.triage != "skip"}
            if need - assigned:
                raise CheckError(f"non-skip sections not assigned to any skill: {sorted(need - assigned)}")
        return sm

    sm = call_json(provider, system_prompt(w, "02_map"), user, parse, stg / "failed", "map")
    (stg / "source_map.json").write_text(sm.model_dump_json(indent=2), encoding="utf-8")
    L = ["# map", "", f"type: {sm.source_type.value}", f"actionable: {sm.actionable}",
         f"gate: {sm.gate_reason}"]
    if sm.triad:
        t = sm.triad
        L.append(f"triad: modular={t.modular} late_binding={t.late_binding} "
                 f"state_transforming={t.state_transforming}{' (' + t.note + ')' if t.note else ''}")
    L += ["", "| section | pages | triage | self-summary | note |", "|---|---|---|---|---|"]
    L += [f"| {c.id} | {c.pages} | {c.triage} | {c.self_summary} | {c.note} |" for c in sm.chapters]
    L += ["", "## Proposed skills"]
    for p in sm.proposed_skills:
        L += [f"- **{p.name}** ({p.role}, {p.artifact}): {p.description}", f"  sections: {', '.join(p.section_ids)}"]
    L += ["", "REVIEW GATE: edit source_map.json (map.md is a rendering), then `skillsmith approve`."]
    (stg / "map.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return _promote(w, "02_map")


# ---------------------------------------------------------------- stage 03
def stage_extract(w: Workspace, provider) -> Path:
    sm = SourceMap.model_validate_json((w.output("02_map") / "source_map.json").read_text(encoding="utf-8"))
    if not sm.actionable:
        raise StageAbstain(f"source not actionable: {sm.gate_reason}")
    secs = {s["id"]: s for s in _sections(w)}
    unknown = [c.id for c in sm.chapters if c.id not in secs]
    unknown += sorted({i for p in sm.proposed_skills for i in p.section_ids if i not in secs})
    if unknown:
        raise StageError(f"source_map.json lists unknown section ids {unknown}; fix the map and re-approve")
    stg = _fresh_staging(w, "03_extract")
    (stg / "units").mkdir()
    tmpl = prompt_template(w, "stage03_extract.md")
    sys_p = system_prompt(w, "03_extract")
    ledger: list[dict] = []
    for ch in sm.chapters:
        if ch.triage == "skip":
            s0 = secs[ch.id]
            ledger.append({"section": ch.id, "title": s0["title"], "triage": "skip", "pdf_pages": s0["pdf_pages"],
                           "units": 0, "status": "skipped_by_map", "reason": ch.note or "triaged skip",
                           "pages_cited": [], "pages_uncited": s0["pdf_pages"]})
            continue
        s = secs[ch.id]
        text = (w.output("01_ingest") / "text" / f"{s['id']}.md").read_text(encoding="utf-8")
        allowed = set(s["pdf_pages"])
        # pdf page -> printed page (None when unknown), straight from the page markers
        printed_for = {int(b): (int(a) if a else None)
                       for a, b in re.findall(r"\[\[(?:printed p\. (\d+) \| )?pdf p\. (\d+)\]\]", text)}
        text_n = _norm(text)
        # per-page text so a quote is checked on the page that is cited, not just somewhere in the section
        parts = re.split(r"\[\[(?:printed p\. \d+ \| )?pdf p\. (\d+)\]\]", text)
        page_text: dict[int, str] = {}
        for i in range(1, len(parts) - 1, 2):
            page_text[int(parts[i])] = page_text.get(int(parts[i]), "") + " " + _norm(parts[i + 1])
        text_nums = set(verify_mod.numbers_in(text)) | {str(p) for p in allowed}
        user = render(tmpl, SECTION_ID=s["id"], TRIAGE=ch.triage,
                      ALLOWED_PAGES=sorted(allowed), SECTION_TEXT=text,
                      SCHEMA=json.dumps(ActionUnit.model_json_schema()))

        def parse(data, allowed=allowed, text_n=text_n, text_nums=text_nums, page_text=page_text):
            reason = None
            if isinstance(data, dict):
                reason = (data.get("no_units_reason") or "").strip() or None
                data = data.get("units", [])
            if not isinstance(data, list):
                raise CheckError('return {"units": [...], "no_units_reason": "..."}')
            units = [ActionUnit.model_validate(d) for d in data]
            if not units and not reason:
                raise CheckError("an empty section needs a no_units_reason: say what it contains and why nothing "
                                 "in it changes what a practitioner would do")
            for u in units:
                for c in u.cites():
                    if c.pdf_page not in allowed:
                        raise CheckError(f"unit '{u.title}': cite pdf_page {c.pdf_page} not in section pdf pages {sorted(allowed)}")
                    known = printed_for.get(c.pdf_page)
                    if c.printed_page is not None and c.printed_page != known:
                        raise CheckError(f"unit '{u.title}': printed_page {c.printed_page} does not match pdf page "
                                         f"{c.pdf_page} (page marker says printed {known if known else 'unknown'}); "
                                         "omit printed_page when unsure")
                    if c.quote_hint:
                        q = _norm(c.quote_hint)
                        window = page_text.get(c.pdf_page, "") + " " + page_text.get(c.pdf_page + 1, "")[:300]
                        if q not in text_n:
                            raise CheckError(f"unit '{u.title}': quote_hint not found verbatim: {c.quote_hint!r}")
                        if q not in window:
                            raise CheckError(
                                f"unit '{u.title}': quote_hint {c.quote_hint!r} is in this section but not on cited "
                                f"pdf page {c.pdf_page}; cite the page where the phrase starts")
                bad = [n for n in verify_mod.numbers_in(u.corpus()) if n not in text_nums]
                if bad:
                    raise CheckError(f"unit '{u.title}': numbers not found in the section text: {bad}. "
                                     "Remove them or move them to `extrapolations`.")
            return units, reason

        units, no_units_reason = call_json(provider, sys_p, user, parse, stg / "failed", f"extract-{s['id']}")
        covered_pages = sorted({c.pdf_page for u in units for c in u.cites()})
        ledger.append({"section": s["id"], "title": s["title"], "triage": ch.triage,
                       "pdf_pages": s["pdf_pages"], "units": len(units), "status": "units" if units else "no_units",
                       "reason": no_units_reason, "pages_cited": covered_pages,
                       "pages_uncited": [p for p in s["pdf_pages"] if p not in covered_pages]})
        for n, u in enumerate(units, 1):
            u.id = f"{s['id']}-u{n:02d}"
            for c in u.cites():
                c.printed_page = printed_for.get(c.pdf_page)  # filled from the page map, never guessed
        (stg / "units" / f"{s['id']}.json").write_text(
            json.dumps([u.model_dump(mode="json") for u in units], indent=2), encoding="utf-8")
        (stg / "units" / f"{s['id']}.md").write_text(_units_md(units, f"Units: {s['title']}"), encoding="utf-8")
    (stg / "coverage.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    rows = ["# coverage ledger (stage 03)", "",
            "Every section is accounted for: extracted, empty with a stated reason, or skipped by the map.", "",
            "| section | triage | status | units | pdf pages with no cited unit | reason |", "|---|---|---|---|---|---|"]
    for r in ledger:
        rows.append(f"| {r['section']} {r['title'][:40]} | {r['triage']} | {r['status']} | {r['units']} | "
                    f"{r['pages_uncited'] if r['pages_uncited'] else '-'} | {r['reason'] or '-'} |")
    (stg / "coverage.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return _promote(w, "03_extract")


# ---------------------------------------------------------------- stage 04
BATCH_TOKENS = 12000  # per-call budget for stage 04; larger skills are consolidated in batches, then merged


def _section_of(unit_id: str) -> str:
    return unit_id.rsplit("-u", 1)[0]


def _consolidate_call(w, provider, prop, units: list[ActionUnit], stg: Path, tag: str) -> ConsolidationResult:
    src_nums = verify_mod.source_numbers(units)
    src_pages = {c.pdf_page for u in units for c in u.cites()}
    by_id = {u.id: u for u in units}
    user = render(prompt_template(w, "stage04_consolidate.md"),
                  PROPOSALS=json.dumps([prop.model_dump()], indent=1),
                  UNITS="\n".join(f"{u.id}: {u.model_dump_json(exclude={'source_units'})}" for u in units),
                  SCHEMA=json.dumps(ConsolidationPlan.model_json_schema()))

    def parse(data) -> ConsolidationResult:
        try:
            r = to_result(ConsolidationPlan.model_validate(data), prop, by_id)
        except PlanError as e:
            raise CheckError(str(e)) from e
        for s in r.skills:
            for u in s.units:  # inherited by construction; a new title is the only model-written text
                bad = [n for n in verify_mod.numbers_in(u.corpus()) if n not in src_nums]
                if bad:
                    raise CheckError(f"{s.name}/'{u.title}': numbers not present in extracted units: {bad}")
                badp = [c.pdf_page for c in u.cites() if c.pdf_page not in src_pages]
                if badp:
                    raise CheckError(f"{s.name}/'{u.title}': cite pdf pages never cited in stage 03: {badp}")
        return r

    return call_json(provider, system_prompt(w, "04_consolidate"), user, parse, stg / "failed", tag)


def stage_consolidate(w: Workspace, provider) -> Path:
    """Hierarchical: one call per proposed skill over only its sections' units;
    skills over the token budget are consolidated in batches, then merged."""
    sm = SourceMap.model_validate_json((w.output("02_map") / "source_map.json").read_text(encoding="utf-8"))
    all_units: list[ActionUnit] = []
    for p in sorted((w.output("03_extract") / "units").glob("*.json")):
        all_units += [ActionUnit.model_validate(d) for d in json.loads(p.read_text(encoding="utf-8"))]
    if not all_units:
        raise StageAbstain("stage 03 produced no action units; nothing to consolidate")
    assigned_sections = {i for p in sm.proposed_skills for i in p.section_ids}
    orphans = sorted({_section_of(u.id) for u in all_units} - assigned_sections)
    if orphans:
        raise StageError(f"stage-03 units in sections {orphans} belong to no proposed skill; "
                         "assign them at the map gate (units would be lost otherwise)")
    stg = _fresh_staging(w, "04_consolidate")
    skills, conflicts, ethics = [], [], []
    for prop in sm.proposed_skills:
        mine = [u for u in all_units if _section_of(u.id) in set(prop.section_ids)]
        if not mine:
            raise StageError(f"no extracted units for proposed skill {prop.name!r}; fix the map at the gate")
        batches, cur = [[]], 0
        for u in mine:
            t = est_tokens_units(u)
            if batches[-1] and cur + t > BATCH_TOKENS:
                batches.append([])
                cur = 0
            batches[-1].append(u)
            cur += t
        parts = [_consolidate_call(w, provider, prop, b, stg, f"consolidate-{prop.name}-b{i}")
                 for i, b in enumerate(batches)]
        if len(parts) == 1:
            r = parts[0]
        else:  # merge pass over the batch results
            merged = [u for pr in parts for s in pr.skills for u in s.units]
            merge_map: dict[str, list[str]] = {}
            for n, u in enumerate(merged, 1):
                u.id = f"merge-u{n:02d}"
                merge_map[u.id] = list(u.source_units)  # original stage-03 ids carried by each batch unit
            r = _consolidate_call(w, provider, prop, merged, stg, f"consolidate-{prop.name}-merge")
            for s in r.skills:  # map merge ids back to the original stage-03 ids
                for u in s.units:
                    u.source_units = expand_merge_ids(u.source_units, merge_map)
                s.excluded = expand_excluded(s.excluded, merge_map)
                for pr in parts:  # exclusions decided in the batch passes already name original ids
                    for ps in pr.skills:
                        s.excluded += ps.excluded
            def _unmerge(text: str, mm=merge_map) -> str:  # internal merge-uNN ids mean nothing to a reviewer
                return re.sub(r"merge-u\d+", lambda m: "/".join(mm.get(m.group(), [m.group()])), text)
            r.conflicts = [_unmerge(c) for c in r.conflicts]
            r.ethics_log = [_unmerge(c) for c in r.ethics_log]
            for pr in parts:
                r.conflicts += pr.conflicts
                r.ethics_log += pr.ethics_log
        for s in r.skills:  # final end-to-end accounting over every original unit of this skill
            missing, unknown = account({u.id for u in mine}, s.units, s.excluded)
            if missing or unknown:
                raise StageError(f"{s.name}: unit accounting failed after merging: missing={sorted(missing)} "
                                 f"unknown={sorted(unknown)}")
        skills += r.skills
        conflicts += r.conflicts
        ethics += r.ethics_log
    (stg / "consolidated").mkdir()
    acct = ["# unit accounting (stage 04)", "",
            "Every stage-03 unit id appears below as carried into a skill unit or excluded with a reason.", ""]
    for s in skills:
        acct.append(f"## {s.name}")
        for n, u in enumerate(s.units, 1):
            u.id = f"u{n:02d}"
            acct.append(f"- {u.id} {u.title}  <=  {', '.join(u.source_units)}")
        for e in s.excluded:
            acct.append(f"- EXCLUDED {e}")
        acct.append("")
    (stg / "accounting.md").write_text("\n".join(acct) + "\n", encoding="utf-8")
    for s in skills:
        (stg / "consolidated" / f"{s.name}.json").write_text(s.model_dump_json(indent=2), encoding="utf-8")
        (stg / "consolidated" / f"{s.name}.md").write_text(_units_md(s.units, f"{s.name}: {s.description}"), encoding="utf-8")
    (stg / "conflicts.md").write_text("# conflicts\n\n" + ("\n".join(f"- {c}" for c in conflicts) or "None flagged.") + "\n", encoding="utf-8")
    (stg / "ethics-log.md").write_text("# ethics-log\n\n" + ("\n".join(f"- {c}" for c in ethics) or "None excluded.") + "\n", encoding="utf-8")
    return _promote(w, "04_consolidate")


def est_tokens_units(u: ActionUnit) -> int:
    return max(1, len(u.model_dump_json()) // 4)


# ---------------------------------------------------------------- stage 05
def source_info(w: Workspace) -> dict:
    """Title, author and file of the source, for attribution in the generated skill. Runs made before this
    existed fall back to reading the PDF's own metadata."""
    meta_f = w.output("01_ingest") / "meta.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.is_file() else {}
    info = {"title": meta.get("source_title", ""), "author": meta.get("source_author", ""), "file": meta.get("source", "")}
    if not info["title"]:
        pdfs = sorted(w.input("01_ingest").glob("*.pdf"))
        if pdfs:
            import pymupdf
            with pymupdf.open(pdfs[0]) as d:
                md = d.metadata or {}
                info["title"] = (md.get("title") or "").strip()
                info["author"] = info["author"] or (md.get("author") or "").strip()
            info["file"] = info["file"] or pdfs[0].name
    pdfs = sorted(w.input("01_ingest").glob("*.pdf"))
    if pdfs:  # provenance: which exact source bytes this skill was compiled from
        import hashlib
        info["sha256"] = hashlib.sha256(pdfs[0].read_bytes()).hexdigest()
    return info


def stage_write(w: Workspace) -> Path:
    specs = sorted((w.output("04_consolidate") / "consolidated").glob("*.json"))
    if not specs:
        raise StageAbstain("no consolidated skills")
    stg = _fresh_staging(w, "05_write")
    report = verify_mod.Report()
    modes: list[str] = []
    exposure: list[str] = []
    source = source_info(w)
    artifacts: dict[str, str] = {}
    sm_f = w.output("02_map") / "source_map.json"
    if sm_f.is_file():
        artifacts = {p.name: p.artifact for p in
                     SourceMap.model_validate_json(sm_f.read_text(encoding="utf-8")).proposed_skills}
    for p in specs:
        spec = verify_mod.load_spec(p)
        spec.artifact = artifacts.get(spec.name, spec.artifact)
        try:
            c = compile_spec(spec, source)
        except CompileError as e:
            raise StageError(str(e)) from e
        d = write_compiled(c, stg, source)
        modes.append(f"- {spec.name}: {spec.artifact}, SKILL.md mode **{c.mode}** ({len(c.skill_md.splitlines())} lines), "
                     f"playbook.md {len(c.playbook_md.splitlines())} lines, {len(spec.units)} units")
        exposure += exposure_report(spec, c)
        r = verify_mod.check_skill_dir(d, spec.units)
        report.checked += r.checked
        report.unsourced += r.unsourced
    (stg / "verify-report.md").write_text(
        report.markdown() + "\n## Compile modes\n"
        "full = everything in SKILL.md; lean = SKILL.md keeps index, steps and defaults; boundaries, pitfalls, "
        "evidence and examples are in playbook.md and references/; index = index only. Nothing is deleted in any mode."
        + "\n\n" + "\n".join(modes) + "\n\n" + "\n".join(exposure) + "\n", encoding="utf-8")
    if report.unsourced:
        raise StageError("unsourced numbers in compiled output (see staging/verify-report.md):\n" + report.summary())
    return _promote(w, "05_write")


# ---------------------------------------------------------------- stage 06
def stage_eval(w: Workspace, provider) -> Path:
    stg = _fresh_staging(w, "06_eval")
    sys_p = system_prompt(w, "06_eval")
    tmpl = prompt_template(w, "stage06_eval.md")
    names = []
    for d in w.skill_dirs():
        spec = verify_mod.load_spec(w.output("04_consolidate") / "consolidated" / f"{d.name}.json")
        skill_text = (d / "SKILL.md").read_text(encoding="utf-8") + "\n" + (d / "playbook.md").read_text(encoding="utf-8")
        skill_low = skill_text.lower()
        user = render(tmpl, NAME=spec.name, DESCRIPTION=spec.description,
                      UNIT_TITLES="; ".join(u.title for u in spec.units), SKILL_TEXT=skill_text,
                      SCHEMA=json.dumps(EvalSet.model_json_schema()))

        def parse(data, spec=spec, skill_low=skill_low) -> EvalSet:
            es = EvalSet.model_validate(data)
            es.skill = spec.name
            low = {p.strip().lower() for p in es.should_fire}
            if any(p.strip().lower() in low for p in es.should_not_fire):
                raise CheckError("a prompt appears in both should_fire and should_not_fire")
            cues = [c.strip() for c in es.cue_words if c.strip()]
            ungrounded = [c for c in cues if c.lower() not in skill_low]
            if ungrounded:
                raise CheckError(f"cue_words not found in the skill text (copy them exactly): {ungrounded}")
            distinct = [c for c in cues if c.lower() not in GENERIC_CUES]
            if len(distinct) < 3:
                raise CheckError("give at least 3 cue_words that are the method's own vocabulary (its name, file names, "
                                 f"named layers or patterns), not everyday words like {sorted(GENERIC_CUES)[:6]}")
            # neutrality is computed here, never taken from the model's own label. A multi-word cue such as
            # "stage contract" also makes its distinctive words ("stage", "contract") off limits.
            watch: list[str] = []
            for c in distinct:
                for w_ in [c.lower()] + [tk for tk in re.findall(r"[a-z0-9]+", c.lower())
                                         if len(tk) >= 4 and tk not in GENERIC_CUES and tk not in CUE_FILLER]:
                    w_ = w_[:-1] if (w_ != c.lower() and w_.endswith("s") and len(w_) > 4) else w_
                    if w_ not in watch:
                        watch.append(w_)

            def leaks(prompt: str) -> list[str]:
                return [c for c in watch if re.search(r"\b" + re.escape(c) + r"\w*", prompt.lower())]

            for t in es.tasks:
                t.neutral = not leaks(t.prompt)
            if sum(t.neutral for t in es.tasks) < 2:
                # targeted repair: rewrite only the leaking prompts, naming the exact forbidden words
                for t in sorted((x for x in es.tasks if not x.neutral), key=lambda x: len(leaks(x.prompt))):
                    if sum(x.neutral for x in es.tasks) >= 2:
                        break
                    for _ in range(2):
                        bad = leaks(t.prompt)
                        try:
                            raw = provider.complete(
                                "You rewrite user requests. Keep the same operational problem, constraints and tone, "
                                "in everyday words. Do NOT use any forbidden word or a close variant (including "
                                "plurals and compounds) and do not add hints about how to solve it. "
                                'Reply with ONLY JSON: {"prompt": "<rewritten request>"}.',
                                f"Forbidden words: {bad}\n\nRequest:\n{t.prompt}")
                            new_p = str(extract_json(raw)["prompt"])
                        except Exception:  # unparseable repair: leave it, the check below will say so
                            break
                        if not leaks(new_p):
                            t.prompt, t.neutral = new_p, True
                            break
                        t.prompt = new_p
            neutral = [t for t in es.tasks if t.neutral]
            if len(neutral) < 2:
                detail = "; ".join(f"task {i + 1} uses {leaks(t.prompt)}" for i, t in enumerate(es.tasks) if not t.neutral)
                raise CheckError(f"only {len(neutral)} task(s) are free of the cue words; at least 2 must be plain "
                                 f"problem statements that never use the method's vocabulary. Rewrite the others: {detail}")
            for t in neutral:
                if not t.baseline_expectation.strip() or not t.treatment_expectation.strip():
                    raise CheckError("every neutral task needs baseline_expectation and treatment_expectation")
            for t in es.tasks:
                bad = [m for m in t.treatment_markers if m.lower() not in skill_low]
                if bad:
                    raise CheckError(f"treatment_markers not found in the skill text: {bad}")
            return es

        es = call_json(provider, sys_p, user, parse, stg / "failed", f"eval-{spec.name}")
        write_evals(es, stg / "evals")
        names.append(spec.name)
    (stg / "eval-report.md").write_text(
        "# eval-report\n\nGenerated trigger and task tests for: " + ", ".join(names) +
        "\n\nStatus: tests WRITTEN, NOT RUN. Run each task with and without the skill and record the "
        "comparison here. On failure, edit the `_config/` file named in each tasks.md, not the skill.\n",
        encoding="utf-8")
    return _promote(w, "06_eval")


# ---------------------------------------------------------------- dispatch
def run_stage(w: Workspace, stage: str, provider=None) -> Path:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; stages: {STAGES}")
    require_prereqs(w, stage, STAGES)
    if stage in ("02_map", "03_extract", "04_consolidate", "06_eval") and provider is None:
        raise StageError(f"{stage} needs an LLM provider")
    if stage == "01_ingest":
        return stage_ingest(w)
    if stage == "02_map":
        return stage_map(w, provider)
    if stage == "03_extract":
        return stage_extract(w, provider)
    if stage == "04_consolidate":
        return stage_consolidate(w, provider)
    if stage == "05_write":
        return stage_write(w)
    return stage_eval(w, provider)

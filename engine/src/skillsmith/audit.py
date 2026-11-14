"""Deterministic audit of a Skillsmith run: coverage ledger, unit accounting, and citation-support checks.

`verify` checks that every number in compiled markdown appears in a cited unit. `audit` checks the next
three questions from the research literature:
1. Coverage vs compression (SPRA arXiv 2610.21424; ICM arXiv 2603.16021): was every section examined, and are
   there non-skipped pages with no cited unit that a human should inspect?
2. Consolidation accounting (SkillAlchemy arXiv 2608.23417): is every stage-03 unit carried into a skill unit
   or explicitly excluded with a reason?
3. Citation support vs citation existence: for each consolidated unit, does the text on the pages it cites
   actually share vocabulary with the unit's procedure steps, or does the citation only back a background
   claim while the steps themselves go beyond that page? This is a lexical screen, not semantic proof: flagged
   units are candidates for human review against `stages/01_ingest/output/pages.jsonl`."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .accounting import account
from .compile import exposure_report, compile_spec
from .runner import source_info
from .schema import ActionUnit, SkillSpec, SourceMap
from .workspace import Workspace

STOP = {
    "the", "and", "for", "with", "that", "this", "when", "from", "into", "your", "have", "what", "how",
    "are", "can", "does", "was", "not", "but", "use", "using", "about", "need", "want", "each", "only",
    "more", "than", "then", "them", "they", "their", "there", "where", "which", "while", "after", "before",
    "between", "under", "over", "such", "same", "other", "some", "any", "all", "both", "one", "two", "three",
    "step", "steps", "make", "made", "give", "given", "keep", "kept", "check", "apply", "applied",
}


def _stem(w: str) -> str:
    for suf in ("ing", "tion", "ions", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _words(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 4 and w not in STOP}


@dataclass
class UnitSupport:
    skill: str
    unit_id: str
    title: str
    cited_pdf_pages: list[int]
    grades: list[str]
    proc_words: int
    overlap_on_cited_pages: float  # fraction of procedure words found on the unit's cited PDF pages
    unbacked_steps: list[str]  # individual steps with <25% word overlap with the cited pages
    quote_hints_checked: int
    quote_hints_missing: list[str]
    verdict: str  # "strong" | "partial" | "weak"


@dataclass
class AuditReport:
    sections_total: int = 0
    sections_extracted: int = 0
    sections_empty_with_reason: int = 0
    sections_skipped: int = 0
    sections_unaccounted: list[str] = field(default_factory=list)
    uncited_pages_by_section: list[tuple[str, str, list[int]]] = field(default_factory=list)
    stage03_units: int = 0
    consolidated_units: int = 0
    excluded_units: int = 0
    accounting_missing: list[str] = field(default_factory=list)
    accounting_unknown: list[str] = field(default_factory=list)
    unit_supports: list[UnitSupport] = field(default_factory=list)
    exposure_lines: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.sections_unaccounted or self.accounting_missing or self.accounting_unknown
                    or any(u.quote_hints_missing for u in self.unit_supports))

    def markdown(self) -> str:
        L = [
            "# Run audit (coverage, accounting, citation support)", "",
            "> What this proves and what it does not: section coverage, unit accounting and `quote_hint` presence "
            "are deterministic checks. Step-to-page word overlap is a lexical screen: a `partial` or `weak` unit "
            "means the procedure uses phrasing not on its cited page (for example synthesized across pages or "
            "rewritten in imperative form), so a human should read that page before relying on the steps.", "",
            "## 1. Section coverage ledger", "",
            f"- Sections in source: **{self.sections_total}** "
            f"(extracted: {self.sections_extracted}, empty with stated reason: {self.sections_empty_with_reason}, "
            f"skipped by map: {self.sections_skipped})",
            f"- Unaccounted sections: **{len(self.sections_unaccounted)}**"
            + (f" ({', '.join(self.sections_unaccounted)})" if self.sections_unaccounted else ""),
        ]
        if self.uncited_pages_by_section:
            L.append("- Non-skipped PDF pages with no cited unit (inspect to confirm nothing actionable was missed):")
            for sec, triage, pgs in self.uncited_pages_by_section:
                L.append(f"  - `{sec}` ({triage}): pdf pages {pgs}")
        else:
            L.append("- Every PDF page of every non-skipped section has at least one cited unit.")
        L += [
            "", "## 2. Stage-03 -> Stage-04 unit accounting", "",
            f"- Stage-03 extracted units: **{self.stage03_units}** -> consolidated into "
            f"**{self.consolidated_units}** skill unit(s), **{self.excluded_units}** excluded with reason",
            f"- Silently dropped units: **{len(self.accounting_missing)}**"
            + (f" ({', '.join(self.accounting_missing)})" if self.accounting_missing else ""),
            f"- Unknown source_unit references: **{len(self.accounting_unknown)}**"
            + (f" ({', '.join(self.accounting_unknown)})" if self.accounting_unknown else ""),
        ]
        if self.exposure_lines:
            L += ["", "## 3. Procedural exposure check (arXiv 2610.26062)", ""] + self.exposure_lines
        L += [
            "", "## 4. Citation support per unit (do the cited pages back the procedure steps?)", "",
            "| unit | title | cited pdf pages | grades | step overlap on cited pages | unbacked steps | verdict |",
            "|---|---|---|---|---|---|---|",
        ]
        for u in self.unit_supports:
            L.append(f"| `{u.unit_id}` | {u.title[:52]} | {u.cited_pdf_pages} | {','.join(u.grades)} | "
                     f"{u.overlap_on_cited_pages:.0%} ({u.proc_words} words) | {len(u.unbacked_steps)} | **{u.verdict}** |")
        weak = [u for u in self.unit_supports if u.verdict != "strong" or u.unbacked_steps or u.quote_hints_missing]
        if weak:
            L += ["", "### Units to inspect against the source PDF"]
            for u in weak:
                L.append(f"- `{u.unit_id}` **{u.title}** (cited pdf pages {u.cited_pdf_pages}, {u.verdict}):")
                for m in u.quote_hints_missing:
                    L.append(f"  - MISSING quote_hint: {m}")
                for s in u.unbacked_steps[:3]:
                    L.append(f"  - low-overlap step: \"{s[:140]}\"")
        return "\n".join(L) + "\n"

    def summary(self) -> str:
        weak = sum(u.verdict == "weak" for u in self.unit_supports)
        part = sum(u.verdict == "partial" for u in self.unit_supports)
        strong = sum(u.verdict == "strong" for u in self.unit_supports)
        status = "OK" if self.ok else "ISSUES"
        return (f"audit {status}: {self.sections_total} sections ({len(self.sections_unaccounted)} unaccounted), "
                f"{self.stage03_units}->{self.consolidated_units} units ({len(self.accounting_missing)} dropped), "
                f"citation support: {strong} strong, {part} partial, {weak} weak")


def _load_pages(w: Workspace) -> dict[int, str]:
    pages_f = w.output("01_ingest") / "pages.jsonl"
    if not pages_f.is_file():
        return {}
    out: dict[int, str] = {}
    for line in pages_f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        txt = d.get("text") or " ".join(d.get("blocks", []))
        out[int(d["pdf_page"])] = txt
    return out


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def audit_workspace(w: Workspace) -> AuditReport:
    rep = AuditReport()
    pages = _load_pages(w)
    cov_f = w.output("03_extract") / "coverage.json"
    secs_f = w.output("01_ingest") / "sections.json"
    if cov_f.is_file() and secs_f.is_file():
        secs = json.loads(secs_f.read_text(encoding="utf-8"))
        cov = json.loads(cov_f.read_text(encoding="utf-8"))
        by_id = {r["section"]: r for r in cov}
        rep.sections_total = len(secs)
        for s in secs:
            r = by_id.get(s["id"])
            if not r:
                rep.sections_unaccounted.append(s["id"])
                continue
            st = r.get("status")
            if st == "units" and r.get("units", 0) > 0:
                rep.sections_extracted += 1
            elif st == "no_units" and (r.get("reason") or "").strip():
                rep.sections_empty_with_reason += 1
            elif st == "skipped_by_map":
                rep.sections_skipped += 1
            else:
                rep.sections_unaccounted.append(s["id"])
            unc = r.get("pages_uncited") or []
            if unc and st != "skipped_by_map":
                rep.uncited_pages_by_section.append((f"{s['id']} {s['title'][:36]}", r.get("triage", "?"), unc))

    s3_units: list[ActionUnit] = []
    units_dir = w.output("03_extract") / "units"
    if units_dir.is_dir():
        for p in sorted(units_dir.glob("*.json")):
            s3_units += [ActionUnit.model_validate(d) for d in json.loads(p.read_text(encoding="utf-8"))]
    rep.stage03_units = len(s3_units)

    cons_dir = w.output("04_consolidate") / "consolidated"
    sm_f = w.output("02_map") / "source_map.json"
    sm = SourceMap.model_validate_json(sm_f.read_text(encoding="utf-8")) if sm_f.is_file() else None
    source = source_info(w)
    if cons_dir.is_dir():
        for p in sorted(cons_dir.glob("*.json")):
            spec = SkillSpec.model_validate_json(p.read_text(encoding="utf-8"))
            rep.consolidated_units += len(spec.units)
            rep.excluded_units += len(spec.excluded)
            if sm:
                prop = next((pr for pr in sm.proposed_skills if pr.name == spec.name), None)
                if prop:
                    spec.artifact = prop.artifact
                    mine = {u.id for u in s3_units if u.id.rsplit("-u", 1)[0] in set(prop.section_ids)}
                    miss, unk = account(mine, spec.units, spec.excluded)
                    rep.accounting_missing += sorted(miss)
                    rep.accounting_unknown += sorted(unk)
            c = compile_spec(spec, source)
            rep.exposure_lines += exposure_report(spec, c)
            for idx, u in enumerate(spec.units, 1):
                uid = u.id or f"u{idx:02d}"
                cites = u.cites()
                pdf_pgs = sorted({ct.pdf_page for ct in cites})
                # include each cited page plus the first 300 chars of the next page (cross-page sentences)
                cited_txt = " ".join(pages.get(pg, "") + " " + pages.get(pg + 1, "")[:300] for pg in pdf_pgs)
                cited_words = _words(cited_txt)
                cited_norm = _norm_ws(cited_txt)
                q_checked, q_missing = 0, []
                for ct in cites:
                    if ct.quote_hint:
                        q_checked += 1
                        w_txt = _norm_ws(pages.get(ct.pdf_page, "") + " " + pages.get(ct.pdf_page + 1, "")[:300])
                        if _norm_ws(ct.quote_hint) not in w_txt:
                            q_missing.append(f"pdf p. {ct.pdf_page}: {ct.quote_hint!r}")
                proc_w = _words(" ".join(u.procedure))
                ov = (len(proc_w & cited_words) / len(proc_w)) if proc_w else 1.0
                unbacked = []
                for step in u.procedure:
                    sw = _words(step)
                    if sw and (len(sw & cited_words) / len(sw)) < 0.25:
                        unbacked.append(step)
                grades = sorted({e.grade.value for e in u.evidence})
                verdict = "strong" if (ov >= 0.45 and not unbacked and not q_missing) else (
                    "partial" if ov >= 0.25 and not q_missing else "weak")
                rep.unit_supports.append(UnitSupport(
                    skill=spec.name, unit_id=uid, title=u.title, cited_pdf_pages=pdf_pgs, grades=grades,
                    proc_words=len(proc_w), overlap_on_cited_pages=ov, unbacked_steps=unbacked,
                    quote_hints_checked=q_checked, quote_hints_missing=q_missing, verdict=verdict))
    if w.stage_dir("05_write").is_dir() and (w.output("05_write")).is_dir():
        (w.output("05_write") / "audit-report.md").write_text(rep.markdown(), encoding="utf-8")
    return rep

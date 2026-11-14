"""SkillSpec -> skill folder: SKILL.md, tool.json, system_prompt.md, playbook.md, references/."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from . import __version__
from .schema import ActionUnit, CompiledSkill, SkillSpec

MAX_LINES = 500
FIT_BOUNDARIES_MAX = 10  # negative boundaries shown in SKILL.md's fit check; the rest stay in playbook.md


class CompileError(Exception):
    pass


# Answer-facing rules. Rewritten after the blind quality run on the ICM skill (runs/icm-paper,
# stages/06_eval/quality): with the skill loaded, answers lost on every neutral task (0 of 6) because
# they imposed the paper's framework on users who never described it, and leaned on page cites from a
# paper the user never mentioned. These rules target those two failures.
USER_RULES = [
    "Fit first: run the fit check below before using any unit. If the user has not described a situation that "
    "matches, solve the problem in the user's own terms first, ask one clarifying question, and offer the method at "
    "most as one option, saying what you are assuming.",
    "Translate, do not transplant: use the user's vocabulary. Bring in a term of the method only when the answer "
    "needs it, and explain it in one line.",
    "Keep the scaffolding internal: Never use unit ids or internal labels in an answer to the user, and do not build "
    "the answer around the source. Name the source (with its page) only when the user asks where advice comes from, "
    "or when a specific number from it matters to the user's decision.",
    "Numbers from the source were measured under the source's conditions: present them as starting points, not "
    "rules, and label anything beyond the source as your own inference.",
    "Finish with something the user can act on for their actual case: concrete next steps or a draft artifact.",
]

ARTIFACT_NOTE = {
    "execution_skill": "This is a procedure: once the fit check passes, follow the matching unit's steps in order.",
    "decision_guide": "This is a decision guide, not a recipe: use its criteria to choose between options and explain "
                      "the trade-off. Do not force a fixed step order on the user.",
    "evidence_reference": "This is an evidence reference: use it to check claims, their evidence grade and the "
                          "conditions they were observed under. It prescribes no procedure; never present it as one.",
}
STEPS_HEADING = {"execution_skill": "Procedure", "decision_guide": "Decision rules",
                 "evidence_reference": "Practices reported in the source (not prescribed)"}

GRADE_LABEL = {"A": "controlled result", "B": "observational or case study", "C": "practitioner heuristic"}
NEGATIVE = re.compile(r"\b(not|never|avoid|unless|only|no|without|weaker|fails?|breaks? down|instead)\b", re.I)
DECISION_TITLE = re.compile(r"^(check|decide|choose|assess|test) (whether|if|which|when)\b", re.I)


def source_line(source: dict | None) -> str:
    if not source or not source.get("title"):
        return ""
    who = f" by {source['author']}" if source.get("author") else ""
    f = f" (file {source['file']})" if source.get("file") else ""
    return (f"Source: *{source['title']}*{who}{f}. Page cites such as (p. N) refer to that document. They are for "
            "checking this skill; cite them in an answer only when the user asks or a number is decisive, and then "
            "name the document in plain words.")


def _cite(c) -> str:
    return f"p. {c.printed_page}" if c.printed_page else f"pdf p. {c.pdf_page}"


def _grade(g) -> str:
    v = getattr(g, "value", g)
    return f"Grade {v} ({GRADE_LABEL.get(v, '?')})"


def _uniq(items):
    seen, out = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _step_key(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", s.lower())).strip()


class _StepDedup:
    """Repeated exposure of the same action makes models favour it regardless of relevance (Procedural
    Exposure Bias, arXiv 2610.26062). In SKILL.md an identical step that already appeared in an earlier unit
    is shown once and referenced afterwards; playbook.md keeps every step in full."""

    def __init__(self) -> None:
        self.first: dict[str, tuple[str, int]] = {}
        self.collapsed = 0

    def render(self, u: ActionUnit) -> list[str]:
        out = []
        for n, step in enumerate(u.procedure, 1):
            k = _step_key(step)
            if k in self.first and self.first[k][0] != u.id:
                uid, m = self.first[k]
                out.append(f"{n}. Same as `{uid}` step {m}.")
                self.collapsed += 1
            else:
                self.first.setdefault(k, (u.id, n))
                out.append(f"{n}. {step}")
        return out


def fit_check(spec: SkillSpec) -> list[str]:
    """Applicability gate rendered at the top of SKILL.md: the source's own decision units plus its
    negative boundaries. Built only from unit text, so every number in it is already sourced."""
    L = ["## Fit check (run before applying anything below)",
         "Apply this skill only when the user's situation matches. If it does not, or the user has not said, "
         "answer in the user's own terms and ask one clarifying question."]
    dec = [u for u in spec.units if DECISION_TITLE.match(u.title)]
    if dec:
        L.append("Decision units to run first: " + "; ".join(f"`{u.id}` {u.title}" for u in dec) + ".")
    neg = _uniq(b for u in spec.units for b in u.boundaries if NEGATIVE.search(b))
    if neg:
        L.append("Do not apply (or adapt first) when:")
        L += [f"- {b}" for b in neg[:FIT_BOUNDARIES_MAX]]
        if len(neg) > FIT_BOUNDARIES_MAX:
            L.append(f"- ...{len(neg) - FIT_BOUNDARIES_MAX} more boundaries in playbook.md.")
    return L + [""]


def _defaults_table(u: ActionUnit) -> list[str]:
    if not u.defaults:
        return []
    L = ["", "| Parameter | Value | Tested range | Source |", "|---|---|---|---|"]
    for d in u.defaults:
        L.append(f"| {d.parameter} | {d.value} | {d.tested_range or '-'} | {_cite(d.cite)} |")
    return L


def _unit_block(u: ActionUnit, playbook: bool = False, dedup: _StepDedup | None = None) -> list[str]:
    L = [f"### {u.title}", f"<!-- unit:{u.id} -->"]
    L.append("When: " + "; ".join(u.triggers))
    L.append("")
    if dedup is not None:
        L += dedup.render(u)
    else:
        for n, step in enumerate(u.procedure, 1):
            L.append(f"{n}. {step}")
    L += _defaults_table(u)
    if playbook:
        L += ["", "Boundaries (where the source says this held; re-check before applying):"] + [f"- {b}" for b in u.boundaries]
        L += ["", "Pitfalls:"] + [f"- {f}" for f in u.failure_modes]
        L += ["", "Evidence behind this unit:"] + [
            f"- {_grade(e.grade)}: {e.claim} ({_cite(e.cite)}). Conditions: {e.conditions}" for e in u.evidence]
    if u.time_sensitive:
        L += ["", "Time-sensitive: check current conditions before reusing these values."]
    for x in u.extrapolations:
        L.append(f"Inference (not stated in the source): {x}")
    L.append("")
    return L


def _how_to_use(spec: SkillSpec, lean: bool) -> list[str]:
    L = ["## How to use", ARTIFACT_NOTE[spec.artifact], ""]
    rules = list(USER_RULES)
    if lean:
        rules.insert(1, "Match the user's situation to one unit in the index below; if none fits, say the situation "
                        "is outside this skill. Before applying a unit, read its boundaries and pitfalls in "
                        "playbook.md (search for its unit id) and do not apply it if a boundary is violated.")
    L += [f"{i}. {r}" for i, r in enumerate(rules, 1)]
    return L + [""]


def render_skill_md(spec: SkillSpec, source: dict | None = None) -> str:
    units = spec.units
    L = ["---", f"name: {spec.name}", f"description: {json.dumps(spec.description)}", "---", "",
         f"# {spec.name.replace('-', ' ').capitalize()}", ""]
    if source_line(source):
        L += [source_line(source), ""]
    L += _how_to_use(spec, lean=False)
    L += fit_check(spec)
    L += ["## When to apply"]
    L += [f"- {t}" for t in _uniq(t for u in units for t in u.triggers)]
    L += ["", "## When NOT to apply"]
    L += [f"- {b}" for b in _uniq(b for u in units for b in u.boundaries)]
    if spec.role == "router":
        L += ["", "## Routing",
              "Diagnose the situation, then hand off to the matching skill. Do not run deep procedures here."]
    evidence = ["", "## Evidence (summary)"]
    for u in units:
        for e in u.evidence:
            evidence.append(f"- {_grade(e.grade)}: {e.claim} ({_cite(e.cite)}). Conditions: {e.conditions}")
    if spec.artifact == "evidence_reference":  # claims lead; practices follow as context only
        L += evidence
    L += ["", f"## {STEPS_HEADING[spec.artifact]}"]
    dedup = _StepDedup()
    for u in units:
        L += _unit_block(u, dedup=dedup)
    L += ["## Failure modes"]
    L += [f"- {f}" for f in _uniq(f for u in units for f in u.failure_modes)]
    if spec.artifact != "evidence_reference":
        L += evidence
    L += ["", "## Worked example"]
    for u in units:
        L.append(f"- Illustrative, not from the source ({u.title}): {u.example}")
    L += ["", "## Going deeper", "- Evidence with page cites: references/evidence.md",
          "- Execution playbook: playbook.md", "- Provenance (source hash, unit lineage): references/provenance.json"]
    if spec.excluded:
        L += ["- Excluded items and why: references/excluded.md"]
    return "\n".join(L) + "\n"


def render_skill_md_lean(spec: SkillSpec, index_only: bool = False, source: dict | None = None) -> str:
    """Progressive disclosure for big skills: SKILL.md is the interface (fit check, index, steps, defaults);
    boundaries, pitfalls, evidence and worked examples stay in playbook.md and references/evidence.md."""
    L = ["---", f"name: {spec.name}", f"description: {json.dumps(spec.description)}", "---", "",
         f"# {spec.name.replace('-', ' ').capitalize()}", "", *([source_line(source), ""] if source_line(source) else [])]
    L += _how_to_use(spec, lean=True)
    L += fit_check(spec)
    L += ["## Unit index"]
    for u in spec.units:
        L.append(f"- `{u.id}` {u.title}. When: {u.triggers[0][:170]}")
    if spec.role == "router":
        L += ["", "## Routing", "Diagnose the situation, then hand off to the matching skill. Do not run deep procedures here."]
    if not index_only:
        L += ["", f"## {STEPS_HEADING[spec.artifact]}"]
        dedup = _StepDedup()
        for u in spec.units:
            L += [f"### {u.title}", f"<!-- unit:{u.id} -->", "When: " + "; ".join(t[:170] for t in u.triggers[:2]), ""]
            L += dedup.render(u)
            L += _defaults_table(u)
            if u.time_sensitive:
                L.append("")
                L.append("Time-sensitive: check current conditions before reusing these values.")
            L += ["", f"Boundaries and pitfalls: playbook.md, unit {u.id}.", ""]
    L += ["## Going deeper", "- Boundaries, pitfalls and worked examples per unit: playbook.md",
          "- Evidence with page cites and the extracted-unit ids behind each unit: references/evidence.md",
          "- Provenance (source hash, unit lineage): references/provenance.json"]
    if spec.excluded:
        L += ["- Excluded items and why: references/excluded.md"]
    return "\n".join(L) + "\n"


def render_playbook(spec: SkillSpec, source: dict | None = None) -> str:
    L = [f"# Playbook: {spec.name}", "", spec.description, "", ARTIFACT_NOTE[spec.artifact], ""]
    if source_line(source):
        L += [source_line(source), ""]
    for u in spec.units:
        L += _unit_block(u, playbook=True)
    return "\n".join(L) + "\n"


def render_evidence(spec: SkillSpec, source: dict | None = None) -> str:
    L = [f"# Evidence: {spec.name}", "", *([source_line(source), ""] if source_line(source) else []),
         "Pages: `p. N` is the printed page of the source edition; `pdf p. N` is used when the printed page is unknown.",
         "Grades: A = controlled result (experiment or proof); B = observational study, case study or un-ablated "
         "benchmark; C = practitioner heuristic or anecdote. Lines marked Inference are not stated in the source.",
         "A page cite shows where a claim was found; it does not prove the claim supports the advice built on it. "
         "Run `skillsmith audit` for a support check.", ""]
    for u in spec.units:
        L.append(f"## {u.title}")
        if u.source_units:
            L.append(f"Built from stage-03 units: {', '.join(u.source_units)}")
        for e in u.evidence:
            hint = f' (locator: "{e.cite.quote_hint}")' if e.cite.quote_hint else ""
            L.append(f"- [{e.grade.value}: {GRADE_LABEL[e.grade.value]}] {e.claim} ({_cite(e.cite)}{hint}). "
                     f"Conditions: {e.conditions}")
        for d in u.defaults:
            L.append(f"- Default {d.parameter} = {d.value} ({_cite(d.cite)})")
        for x in u.extrapolations:
            L.append(f"- Inference (not in the source): {x}")
        L.append("")
    return "\n".join(L)


def tool_schema(spec: SkillSpec) -> dict:
    ids = [u.id for u in spec.units if u.id]
    props: dict = {"situation": {"type": "string",
                                 "description": "The user's situation in one or two sentences."}}
    if ids:
        props["unit_id"] = {"type": "string", "enum": ids,
                            "description": "Optional: return only this action unit."}
    return {"name": spec.name, "description": spec.description,
            "input_schema": {"type": "object", "properties": props, "required": ["situation"]}}


def render_system_prompt(spec: SkillSpec, source: dict | None = None) -> str:
    titles = "\n".join(f"- {u.id}: {u.title}" for u in spec.units)
    return (
        f"You have the `{spec.name}` skill ({spec.artifact}).\n\n"
        f"Use it when: {spec.description}\n\n"
        f"{ARTIFACT_NOTE[spec.artifact]}\n\n"
        "How to use it:\n"
        "1. Run the fit check first: match the user's situation to one unit below; if none fits, or a boundary is "
        "violated, solve the user's problem in their own terms and say why the playbook may not apply.\n"
        "2. Use the unit's defaults only inside the stated boundaries, as starting points.\n"
        + "".join(f"{i + 3}. {r}\n" for i, r in enumerate(USER_RULES))
        + (f"\n{source_line(source)}\n" if source_line(source) else "")
        + f"\nUnits:\n{titles}\n"
    )


def provenance_record(spec: SkillSpec, c: CompiledSkill, source: dict | None = None) -> dict:
    """Lineage of a compiled skill so future runs can see what source version and which extracted units
    each skill unit came from (WikiSkill arXiv 2608.27454; How Agent Skills Evolve arXiv 2611.04456)."""
    src = source or {}
    return {
        "skill": spec.name,
        "artifact": spec.artifact,
        "role": spec.role,
        "compile_mode": c.mode,
        "skillsmith_version": __version__,
        "source": {"title": src.get("title", ""), "author": src.get("author", ""),
                   "file": src.get("file", ""), "sha256": src.get("sha256", "")},
        "units": [
            {"id": u.id, "title": u.title, "source_units": list(u.source_units),
             "pdf_pages": sorted({ct.pdf_page for ct in u.cites()}),
             "printed_pages": sorted({ct.printed_page for ct in u.cites() if ct.printed_page is not None}),
             "evidence_grades": sorted({e.grade.value for e in u.evidence})}
            for u in spec.units
        ],
        "excluded": list(spec.excluded),
    }


def exposure_report(spec: SkillSpec, c: CompiledSkill) -> list[str]:
    """Check whether any step is repeated across units in the compiled skill (Procedural Exposure Bias,
    arXiv 2610.26062: repeated exposure of an action pattern increases a model's preference for it even
    when relevance is unchanged)."""
    counts = Counter(_step_key(s) for u in spec.units for s in u.procedure if _step_key(s))
    dups = {k: v for k, v in counts.items() if v > 1}
    dedup = _StepDedup()
    for u in spec.units:
        dedup.render(u)
    if not dups:
        return [f"- {spec.name} exposure check: no step repeated across units."]
    return [f"- {spec.name} exposure check: {len(dups)} step pattern(s) appeared in >1 unit; "
            f"collapsed {dedup.collapsed} duplicate exposure(s) in SKILL.md (full steps kept in playbook.md)."]


def compile_spec(spec: SkillSpec, source: dict | None = None) -> CompiledSkill:
    for n, u in enumerate(spec.units, 1):
        if not u.id:
            u.id = f"u{n:02d}"
    md, mode = render_skill_md(spec, source), "full"
    if len(md.splitlines()) > MAX_LINES:  # progressive disclosure before giving up: nothing is deleted
        md, mode = render_skill_md_lean(spec, source=source), "lean"
    if len(md.splitlines()) > MAX_LINES:
        md, mode = render_skill_md_lean(spec, index_only=True, source=source), "index"
    if len(md.splitlines()) > MAX_LINES:
        raise CompileError(
            f"{spec.name}: even the index-only SKILL.md exceeds {MAX_LINES} lines; split the skill at the map gate")
    return CompiledSkill(spec=spec, skill_md=md, mode=mode, tool_schema=tool_schema(spec),
                         system_prompt=render_system_prompt(spec, source),
                         playbook_md=render_playbook(spec, source), evidence_md=render_evidence(spec, source))


def write_compiled(c: CompiledSkill, out_dir: Path, source: dict | None = None) -> Path:
    d = Path(out_dir) / c.spec.name
    (d / "references").mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(c.skill_md, encoding="utf-8")
    (d / "playbook.md").write_text(c.playbook_md, encoding="utf-8")
    (d / "system_prompt.md").write_text(c.system_prompt, encoding="utf-8")
    (d / "tool.json").write_text(json.dumps(c.tool_schema, indent=2), encoding="utf-8")
    (d / "references" / "evidence.md").write_text(c.evidence_md, encoding="utf-8")
    (d / "references" / "provenance.json").write_text(
        json.dumps(provenance_record(c.spec, c, source), indent=2), encoding="utf-8")
    if c.spec.excluded:
        (d / "references" / "excluded.md").write_text(
            "# Excluded\n\n" + "\n".join(f"- {x}" for x in c.spec.excluded) + "\n", encoding="utf-8")
    cands = [u for u in c.spec.units if u.script_candidate]
    if cands:
        (d / "references" / "script-candidates.md").write_text(
            "# Deterministic steps to turn into scripts/\n\n"
            + "\n".join(f"- {u.id}: {u.title}" for u in cands) + "\n", encoding="utf-8")
    return d

"""Deterministic number-to-source checker. No LLM."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .schema import ActionUnit, SkillSpec

# digits not glued to letters/underscore/hyphen/dot (skips ids like ch05-u02, 01_ingest, v1.2.3)
NUM = re.compile(r"(?<![\w.])\$?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?|\.\d+)%?(?![\d_]|\.\d)")
# references, not values: "Fig. 3", "Table 2", "Section 4.2", "step 1", "page 12", unit ids "u01"
REF = re.compile(r"\b(?:fig(?:ure)?s?|tables?|sections?|sec|steps?|pages?|eq(?:uation)?s?|chapters?)\.?\s*\d+(?:\.\d+)*|\bu\d{2}\b", re.I)
RANGE_DASH = re.compile(r"(?<=\d)\s*[-–]\s*(?=\d)")  # "15-25" -> two numbers
PAGE_CITE = re.compile(r"\bpp?\.\s*\d+(?:\s*[-–]\s*\d+)?", re.I)
MORE_BOUNDARIES = re.compile(r"\.\.\.\d+ more boundaries in playbook\.md")
LIST_MARKER = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+")
EXAMPLE_HEAD = re.compile(r"^#{1,6}\s*(worked example|illustrative example)s?\s*$", re.I)
HEAD = re.compile(r"^#{1,6}\s")


def norm(tok: str) -> str:
    t = tok.replace("$", "").replace(",", "").rstrip("%").rstrip(".")
    return "0" + t if t.startswith(".") else t


def numbers_in(text: str) -> list[str]:
    text = REF.sub(" ", RANGE_DASH.sub(" ", text))
    return [norm(m.group()) for m in NUM.finditer(text)]


def source_numbers(units: list[ActionUnit]) -> set[str]:
    """Numbers that appear in unit text. Page numbers are NOT sources of values:
    a cite on p. 12 must not legitimise 'use 12 chunks'. (Page cites are stripped
    from checked text separately.)"""
    s: set[str] = set()
    for u in units:
        s.update(numbers_in(u.corpus()))
    return s


@dataclass
class Unsourced:
    file: str
    line: int
    number: str
    text: str


@dataclass
class Report:
    checked: int = 0
    unsourced: list[Unsourced] = field(default_factory=list)

    def summary(self) -> str:
        if not self.unsourced:
            return f"verify OK: {self.checked} numbers checked, all sourced"
        rows = [f"verify FAILED: {len(self.unsourced)} unsourced of {self.checked} numbers"]
        rows += [f"  {u.file}:{u.line}: {u.number!r} in: {u.text.strip()[:90]}" for u in self.unsourced]
        return "\n".join(rows)

    def markdown(self) -> str:
        if not self.unsourced:
            return f"# verify-report\n\nAll {self.checked} numbers trace to a unit with a page cite.\n"
        body = "\n".join(f"- `{u.file}:{u.line}` number `{u.number}`: {u.text.strip()[:120]}"
                         for u in self.unsourced)
        return f"# verify-report\n\n{len(self.unsourced)} unsourced of {self.checked}:\n\n{body}\n"


def check_text(text: str, sources: set[str], file: str = "") -> Report:
    rep = Report()
    in_fm = False
    in_code = False
    skip_section = False
    for i, line in enumerate(text.splitlines(), 1):
        if i == 1 and line.strip() == "---":
            in_fm = True
            continue
        if in_fm:
            if line.strip() == "---":
                in_fm = False
            continue
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if HEAD.match(line):
            skip_section = bool(EXAMPLE_HEAD.match(line))
            line = HEAD.sub("", line)
            if skip_section:
                continue
        if skip_section or "<!--" in line or line.startswith("Source:"):
            continue
        clean = LIST_MARKER.sub("", line)
        clean = MORE_BOUNDARIES.sub("", PAGE_CITE.sub("", clean))
        for tok in numbers_in(clean):
            rep.checked += 1
            if tok not in sources:
                rep.unsourced.append(Unsourced(file, i, tok, line))
    return rep


def check_skill_dir(skill_dir: Path, units: list[ActionUnit]) -> Report:
    sources = source_numbers(units)
    total = Report()
    for name in ("SKILL.md", "playbook.md", "system_prompt.md"):
        p = skill_dir / name
        if p.is_file():
            r = check_text(p.read_text(encoding="utf-8"), sources, f"{skill_dir.name}/{name}")
            total.checked += r.checked
            total.unsourced += r.unsourced
    return total


def load_spec(path: Path) -> SkillSpec:
    return SkillSpec.model_validate(json.loads(path.read_text(encoding="utf-8")))


def check(w) -> Report:
    """Verify every compiled skill in stage 05 against its consolidated SkillSpec."""
    if not w.done("05_write"):
        raise RuntimeError("stage 05_write is not done (missing or stale after an upstream re-run); run it before verify")
    total = Report()
    specs = {p.stem: p for p in (w.output("04_consolidate") / "consolidated").glob("*.json")}
    for d in w.skill_dirs():
        if d.name not in specs:
            total.unsourced.append(Unsourced(d.name, 0, "-", "no consolidated spec for this skill"))
            continue
        r = check_skill_dir(d, load_spec(specs[d.name]).units)
        total.checked += r.checked
        total.unsourced += r.unsourced
    return total

"""Scripted fake LLM that reads the real stage prompts and answers deterministically."""
from __future__ import annotations

import json
import re

from skillsmith.llm import FakeProvider

NAME = "long-doc-retrieval"
DESC = "Use when building retrieval over long documents, choosing chunk sizes, or when answers miss information spread across sections."


def _map(user: str) -> str:
    rows = re.findall(r"^(ch\d+(?:-p\d+)?) \| (.*?) \| (\S+) \|", user, re.M)
    chapters = [{"id": i, "pages": pg, "self_summary": False,
                 "triage": "skip" if t.lower().startswith("front") else "procedure"}
                for i, t, pg in rows]
    keep = [c["id"] for c in chapters if c["triage"] != "skip"]
    return json.dumps({"source_type": "method", "actionable": True,
                       "gate_reason": "A practitioner would build a summary tree for long-document retrieval.",
                       "triad": {"modular": True, "late_binding": True, "state_transforming": True,
                                 "note": "Externalized procedure loaded on retrieval questions."},
                       "chapters": chapters,
                       "proposed_skills": [{"name": NAME, "description": DESC, "role": "standard",
                                            "artifact": "execution_skill", "section_ids": keep}]})


def _extract(user: str) -> str:
    sid = re.search(r"Section id: (\S+)", user).group(1)
    pages = json.loads(re.search(r"Allowed PDF pages for citations: (\[.*?\])", user).group(1))
    body = user.split("Section text:", 1)[1].split("Return ONLY", 1)[0]
    body = re.sub(r"\[\[[^\]]*\]\]", " ", body)
    nums = re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])", body)
    default = nums[-1] if nums else None
    unit = {"title": f"Apply guidance of {sid}", "triggers": ["long-document retrieval question"],
            "procedure": ["Read the guidance.", "Apply it to the retrieval design."],
            "defaults": ([{"parameter": "value", "value": default,
                           "cite": {"pdf_page": pages[0]}}] if default else []),
            "boundaries": ["Only within the conditions the source states."],
            "failure_modes": ["Applying the default outside its tested range."],
            "evidence": [{"claim": "The source reports this guidance.", "grade": "C",
                          "conditions": "single synthetic source", "cite": {"pdf_page": pages[0]}}],
            "example": "A user asks how to index a long contract archive."}
    return json.dumps([unit])


def _consolidate(user: str) -> str:
    """Fake model: a plan that keeps every unit as its own plan unit."""
    name = re.search(r'"name": "([^"]+)"', user).group(1)
    ids = []
    for line in user.split("Extracted units for this skill (id: JSON):", 1)[1].splitlines():
        m = re.match(r"^(\S+-u\d+): \{", line.strip())
        if m:
            ids.append(m.group(1))
    return json.dumps({"skills": [{"name": name, "units": [{"primary": i} for i in ids]}],
                       "conflicts": [], "ethics_log": []})


def _eval(user: str) -> str:
    neutral = {"prompt": "I have a pile of eight pages of notes and need a repeatable way to turn them into answers.",
               "expected_differences": ["cites a page"], "neutral": True,
               "baseline_expectation": "a generic summary script", "treatment_expectation": "applies the guidance units",
               "baseline_markers": ["pip install"], "treatment_markers": ["guidance"]}
    return json.dumps({"skill": "x",
                       "should_fire": [f"fire prompt {i}" for i in range(10)],
                       "should_not_fire": [f"near miss {i}" for i in range(10)],
                       "cue_words": ["retrieval", "guidance", "default", "tested range", "conditions"],
                       "tasks": [dict(neutral, prompt=neutral["prompt"] + f" Variant {i}.") for i in range(2)] +
                                [{"prompt": "task 3 about retrieval guidance", "expected_differences": ["cites a page"]}]})


def responder(system: str, user: str) -> str:
    if "stage 02_map" in user:
        return _map(user)
    if "stage 03_extract" in user:
        return _extract(user)
    if "stage 04_consolidate" in user:
        return _consolidate(user)
    if "stage 06_eval" in user:
        return _eval(user)
    raise AssertionError("unrecognized stage prompt")


def fake() -> FakeProvider:
    return FakeProvider(responder)

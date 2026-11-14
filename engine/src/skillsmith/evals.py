"""Render a validated EvalSet to evals/<skill>/{eval.json, triggers.md, tasks.md}."""
from __future__ import annotations

import json
from pathlib import Path

from .schema import EvalSet


def write_evals(es: EvalSet, out_dir: Path) -> None:
    d = Path(out_dir) / es.skill
    d.mkdir(parents=True, exist_ok=True)
    (d / "eval.json").write_text(es.model_dump_json(indent=2), encoding="utf-8")  # machine-readable, for eval-run
    t = [f"# Trigger tests: {es.skill}", "", "## Should fire"] + [f"- {p}" for p in es.should_fire]
    t += ["", "## Near-miss, should NOT fire"] + [f"- {p}" for p in es.should_not_fire]
    (d / "triggers.md").write_text("\n".join(t) + "\n", encoding="utf-8")
    k = [f"# Task tests: {es.skill}", "", "Run each with and without the skill; compare.",
         f"Cue words (neutral tasks must not use these): {', '.join(es.cue_words)}", ""]
    for i, task in enumerate(es.tasks, 1):
        tags = [lbl for lbl, ok in (("neutral", task.neutral), ("near-miss: do NOT apply", not task.expect_apply)) if ok]
        tag = f" ({', '.join(tags)})" if tags else ""
        k += [f"## Task {i}{tag}", task.prompt, ""]
        if task.baseline_expectation:
            k += [f"Expected without the skill: {task.baseline_expectation}"]
        if task.treatment_expectation:
            k += [f"Expected with the skill: {task.treatment_expectation}"]
        if task.baseline_markers:
            k += [f"Baseline markers: {', '.join(task.baseline_markers)}"]
        if task.treatment_markers:
            k += [f"Treatment markers: {', '.join(task.treatment_markers)}"]
        k += ["", "Expected differences with the skill:"]
        k += [f"- {x}" for x in task.expected_differences]
        if task.process_checks:
            k += ["", "Process checks (strict = all must pass, SkillForgeBench 2610.14918):"]
            k += [f"- {x}" for x in task.process_checks]
        k += [""]
    k += [f"On failure edit: `{es.config_file_to_edit_on_failure}`"]
    (d / "tasks.md").write_text("\n".join(k) + "\n", encoding="utf-8")

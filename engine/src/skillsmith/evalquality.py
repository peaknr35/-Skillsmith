"""Blind answer-quality comparison: does the skill-loaded answer solve the user's problem better?

Unlike evalrun's task comparison, the judge here never sees the skill's vocabulary or any
skill-specific rubric. The criteria are fixed in this file BEFORE any output is judged:
solves the stated problem, fits the stated constraints, identifies risks and limits,
actionability, honesty about uncertainty. Each task is answered `repeats` times per condition;
every pair is shown in random order as Option 1 / Option 2.

Honest limits, repeated in every report: small samples; a model judge; treatment answers often
carry visible markers (unit ids, page cites), so blindness is partial; the generator and the
judge may share a model family; the tasks come from the same pipeline that built the skill."""
from __future__ import annotations

import json
import math
import random
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .evalrun import BASELINE_SYSTEM, EvalRunError, _call, load_eval
from .runner import extract_json
from .schema import EvalSet
from .workspace import Workspace

CRITERIA = {
    "solves_problem": "Addresses the user's actual question and gives an answer that would solve their stated problem.",
    "fits_constraints": "Respects every constraint the user stated (people involved, review requirements, scale, tools, effort).",
    "risks_and_limits": "Names realistic risks, trade-offs and the conditions under which its advice would not hold.",
    "actionability": "Gives concrete steps the user could carry out next, not generalities.",
    "honesty": "Does not present invented specifics as fact; flags what it does not know or is assuming.",
}

JUDGE_SYSTEM = (
    "You are an impartial senior reviewer. You will see a user's request and two candidate answers, Option 1 and "
    "Option 2. Judge ONLY how well each answer helps this user. Do not try to guess how either answer was produced, "
    "and do not reward length, formatting or confident tone for their own sake. Score each option from 1 (poor) to 5 "
    "(excellent) on these criteria:\n"
    + "\n".join(f"- {k}: {v}" for k, v in CRITERIA.items())
    + '\nThen choose the better answer overall for this user: "1", "2" or "tie". Reply with ONLY JSON: '
      '{"option1": {"solves_problem": n, "fits_constraints": n, "risks_and_limits": n, "actionability": n, "honesty": n}, '
      '"option2": {...same keys...}, "preferred": "1" | "2" | "tie", "reason": "<one sentence>"}'
)

MARKER = re.compile(r"\b[uU]\d{2}\b|\(p\. ?\d+\)|\bp\. \d+\b")


def sign_test_p(wins: int, losses: int) -> float | None:
    """Exact two-sided sign test on non-tied comparisons; None when there is nothing to test."""
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def judge_pair(provider, request: str, opt1: str, opt2: str) -> dict:
    user = f"User request:\n{request}\n\n=== Option 1 ===\n{opt1}\n\n=== Option 2 ===\n{opt2}\n"
    raw = _call(provider, JUDGE_SYSTEM, user)
    try:
        d = extract_json(raw)
        scores = {}
        for opt in ("option1", "option2"):
            scores[opt] = {k: float(d[opt][k]) for k in CRITERIA}
        pref = str(d.get("preferred", "tie")).strip()
        if pref not in ("1", "2", "tie"):
            pref = "tie"
        return {"scores": scores, "preferred": pref, "reason": str(d.get("reason", ""))[:300], "ok": True}
    except (ValueError, KeyError, TypeError, AttributeError):
        return {"ok": False, "error": raw[:200]}


def _one_rep(gen, judge, request, treatment_system, task_i, rep, out_dir, rng_seed):
    base = _call(gen, BASELINE_SYSTEM, request)
    treat = _call(gen, treatment_system, request)
    (out_dir / f"task_{task_i:02d}_rep{rep}_baseline.md").write_text(f"# Task {task_i} rep {rep} baseline\n\n{request}\n\n---\n\n{base}\n", encoding="utf-8")
    (out_dir / f"task_{task_i:02d}_rep{rep}_treatment.md").write_text(f"# Task {task_i} rep {rep} treatment\n\n{request}\n\n---\n\n{treat}\n", encoding="utf-8")
    treat_first = random.Random(rng_seed).random() < 0.5  # which answer is shown as Option 1
    o1, o2 = (treat, base) if treat_first else (base, treat)
    j = judge_pair(judge, request, o1, o2)
    row = {"task": task_i, "rep": rep, "treatment_first": treat_first, "ok": j["ok"],
           "baseline_chars": len(base), "treatment_chars": len(treat),
           "treatment_markers_visible": bool(MARKER.search(treat)), "baseline_markers_visible": bool(MARKER.search(base))}
    if not j["ok"]:
        row["error"] = j["error"]
        return row
    s = j["scores"]
    tr, ba = (s["option1"], s["option2"]) if treat_first else (s["option2"], s["option1"])
    pref = j["preferred"]
    winner = "tie" if pref == "tie" else ("treatment" if (pref == "1") == treat_first else "baseline")
    row.update({"winner": winner, "scores_treatment": tr, "scores_baseline": ba, "reason": j["reason"]})
    return row


def quality_comparison(gen, judge, skill_dir: Path, es: EvalSet, out_dir: Path, repeats: int = 3,
                       with_playbook: bool = True, seed: int = 0, workers: int = 4) -> list[dict]:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    if with_playbook:  # the intended retrieval path: the model has read the playbook for the unit it applies
        skill_text += "\n\n" + (skill_dir / "playbook.md").read_text(encoding="utf-8")
    treatment_system = (BASELINE_SYSTEM + "\n\nA skill is loaded for this conversation. Apply it when the request "
                        "falls within its description.\n\n" + skill_text)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for i, t in enumerate(es.tasks, 1):
        for rep in range(1, repeats + 1):
            jobs.append((t.prompt, treatment_system, i, rep, out_dir, seed * 100003 + i * 101 + rep))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futures = [ex.submit(_one_rep, gen, judge, *j) for j in jobs]
        rows = [f.result() for f in futures]
    neutral = {i: t.neutral for i, t in enumerate(es.tasks, 1)}
    for r in rows:
        r["neutral"] = neutral[r["task"]]
    return rows


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("ok")]

    def block(sub):
        w = sum(r["winner"] == "treatment" for r in sub)
        l = sum(r["winner"] == "baseline" for r in sub)
        t = sum(r["winner"] == "tie" for r in sub)
        means = {}
        for cond in ("treatment", "baseline"):
            means[cond] = {k: (sum(r[f"scores_{cond}"][k] for r in sub) / len(sub)) if sub else None for k in CRITERIA}
        return {"n": len(sub), "treatment_wins": w, "baseline_wins": l, "ties": t, "sign_test_p": sign_test_p(w, l),
                "mean_scores": means}

    return {"all": block(ok), "neutral_only": block([r for r in ok if r["neutral"]]),
            "failed_judgments": len(rows) - len(ok),
            "mean_chars": {"baseline": sum(r["baseline_chars"] for r in rows) / len(rows) if rows else 0,
                           "treatment": sum(r["treatment_chars"] for r in rows) / len(rows) if rows else 0},
            "treatment_answers_with_visible_markers": sum(r["treatment_markers_visible"] for r in rows),
            "baseline_answers_with_visible_markers": sum(r["baseline_markers_visible"] for r in rows),
            "n_rows": len(rows)}


def render_report(skill: str, gen_model: str, judge_model: str, repeats: int, with_playbook: bool, s: dict) -> str:
    def fmt(b):
        p = b["sign_test_p"]
        return (f"treatment preferred {b['treatment_wins']}, baseline preferred {b['baseline_wins']}, tie {b['ties']} "
                f"(n={b['n']}); exact sign test p = {'n/a' if p is None else f'{p:.3f}'}")

    L = [f"# Blind quality judgement: {skill}", "",
         f"Generator: {gen_model}. Judge: {judge_model}. {repeats} repeat(s) per task. Treatment context: SKILL.md"
         f"{' + playbook.md' if with_playbook else ' only'}.", "",
         "> Limits: small samples; a model judge; treatment answers often carry visible markers (unit ids, page cites), so the "
         "judge is only partly blind; the generator and judge may share a model family; the tasks were generated by the "
         "pipeline that built the skill. A model preference is a signal, not proof that the advice is better. Read the saved "
         "answers.", "",
         "Criteria (fixed in code before judging, none mention the skill): " + "; ".join(CRITERIA), "",
         "## Overall preference", "", f"- All tasks: {fmt(s['all'])}", f"- Neutral tasks only: {fmt(s['neutral_only'])}",
         f"- Judgments that failed to parse: {s['failed_judgments']}", "",
         "## Mean scores (1-5)", "", "| criterion | without skill | with skill | without (neutral only) | with (neutral only) |", "|---|---|---|---|---|"]
    for k in CRITERIA:
        a, n = s["all"]["mean_scores"], s["neutral_only"]["mean_scores"]
        f2 = lambda v: "n/a" if v is None else f"{v:.2f}"
        L.append(f"| {k} | {f2(a['baseline'][k])} | {f2(a['treatment'][k])} | {f2(n['baseline'][k])} | {f2(n['treatment'][k])} |")
    L += ["", "## Confounds to read next to the numbers", "",
          f"- Mean answer length: {s['mean_chars']['baseline']:.0f} characters without the skill, {s['mean_chars']['treatment']:.0f} with it.",
          f"- Answers showing unit ids or page cites (visible markers): {s['treatment_answers_with_visible_markers']} of {s['n_rows']} with the skill, "
          f"{s['baseline_answers_with_visible_markers']} of {s['n_rows']} without.", ""]
    return "\n".join(L)


def run(w: Workspace, gen, judge, skill: str | None = None, gen_model: str = "", judge_model: str = "",
        repeats: int = 3, with_playbook: bool = True, workers: int = 4, eval_file: Path | None = None) -> Path:
    """eval_file: judge a rebuilt skill on a FROZEN eval set (an earlier eval.json) so before/after is comparable;
    re-running stage 05 marks stage 06 stale, which would otherwise block this."""
    if eval_file is None and not w.done("06_eval"):
        raise EvalRunError("stage 06_eval is not done")
    d = next((x for x in w.skill_dirs() if skill in (None, x.name)), None)
    if d is None:
        raise EvalRunError(f"skill {skill!r} not found")
    es = EvalSet.model_validate_json(Path(eval_file).read_text(encoding="utf-8")) if eval_file else load_eval(w, d.name)
    run_dir = w.stage_dir("06_eval") / "quality" / d.name / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = quality_comparison(gen, judge, d, es, run_dir, repeats, with_playbook, workers=workers)
    s = summarize(rows)
    (run_dir / "results.json").write_text(json.dumps({"rows": rows, "summary": s}, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(render_report(d.name, gen_model, judge_model, repeats, with_playbook, s), encoding="utf-8")
    return run_dir

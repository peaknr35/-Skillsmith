"""Stage-06 neutral-task rules and the eval harness (fake model: these test the harness, not the skill)."""
import json
import re

import pytest

from skillsmith import cli, evalrun, gates, runner
from skillsmith.llm import FakeProvider

from .fakes import fake, responder
from .test_integration import run_all


def _eval_dict(user):
    return json.loads(responder("", user))


def _upto_05(ws):
    prov = fake()
    runner.run_stage(ws, "01_ingest")
    runner.run_stage(ws, "02_map", prov)
    gates.approve(ws, "02_map")
    runner.run_stage(ws, "03_extract", prov)
    runner.run_stage(ws, "04_consolidate", prov)
    gates.approve(ws, "04_consolidate")
    runner.run_stage(ws, "05_write")


def _stage06_with(ws, mutate):
    def resp(s, u):
        if "stage 06_eval" in u:
            d = json.loads(responder(s, u))
            mutate(d)
            return json.dumps(d)
        return responder(s, u)

    return FakeProvider(resp)


def test_neutrality_is_computed_from_the_prompt_not_trusted_from_the_model(ws):
    _upto_05(ws)

    def leak_one(d):  # task 1 uses the cue word 'retrieval'; task 3 already does; only task 2 stays neutral
        d["tasks"][0]["prompt"] = "I want a retrieval pipeline for eight pages of notes."

    with pytest.raises(runner.StageError, match="only 1 task.*free of the cue words.*task 1 uses"):
        runner.run_stage(ws, "06_eval", _stage06_with(ws, leak_one))

    def lie(d):  # the model labels everything neutral; the code must not believe it
        for t in d["tasks"]:
            t["neutral"] = True
        d["tasks"][1]["prompt"] += " Use retrieval."

    with pytest.raises(runner.StageError, match="free of the cue words"):
        runner.run_stage(ws, "06_eval", _stage06_with(ws, lie))


def test_everyday_words_cannot_be_the_only_cue_words(ws, monkeypatch):
    monkeypatch.setattr(runner, "GENERIC_CUES", runner.GENERIC_CUES | {"design", "question"})  # words in the fixture skill
    _upto_05(ws)

    def generic(d):
        d["cue_words"] = ["design", "question", "retrieval"]  # only 'retrieval' is distinctive

    with pytest.raises(runner.StageError, match="method's own vocabulary"):
        runner.run_stage(ws, "06_eval", _stage06_with(ws, generic))

    def generic_plus_real(d):
        d["cue_words"] = ["design", "question", "retrieval", "guidance", "default"]  # 3 distinctive ones: fine

    runner.run_stage(ws, "06_eval", _stage06_with(ws, generic_plus_real))
    es = json.loads(next((ws.output("06_eval") / "evals").glob("*/eval.json")).read_text())
    assert sum(t["neutral"] for t in es["tasks"]) >= 2


def test_ungrounded_cue_word_or_marker_is_rejected(ws):
    _upto_05(ws)

    def bad_cue(d):
        d["cue_words"].append("quantum-widget")

    with pytest.raises(runner.StageError, match="cue_words not found in the skill text"):
        runner.run_stage(ws, "06_eval", _stage06_with(ws, bad_cue))

    def bad_marker(d):
        d["tasks"][2]["treatment_markers"] = ["invented-term"]

    with pytest.raises(runner.StageError, match="treatment_markers not found"):
        runner.run_stage(ws, "06_eval", _stage06_with(ws, bad_marker))


def test_valid_eval_set_is_written_with_machine_readable_json(ws):
    run_all(ws)
    d = ws.output("06_eval") / "evals" / "long-doc-retrieval"
    es = json.loads((d / "eval.json").read_text())
    assert sum(t["neutral"] for t in es["tasks"]) >= 2 and es["cue_words"]
    assert "(neutral)" in (d / "tasks.md").read_text()


# ---------------------------------------------------------------- harness
def harness_responder(system, user):
    if system.startswith("You route user requests"):
        names = re.findall(r"^- ([a-z0-9\-]+):", system, re.M)
        mine = [n for n in names if n not in {d[0] for d in evalrun.DEFAULT_DISTRACTORS}][0]
        return json.dumps({"selected_skill": mine if user.startswith("fire prompt") else "none"})
    if system.startswith("You are a strict"):
        assert "baseline" not in user.lower() and "treatment" not in user.lower()  # blind
        parts = re.split(r"=== Option [12] ===", user)
        o1, o2 = parts[1], parts[2]
        n = len(re.findall(r"^\d+\. ", user.split("Behaviours to check:")[1].split("=== Option 1")[0], re.M))
        rows = [{"behaviour": f"b{i}", "option1": "guidance" in o1, "option2": "guidance" in o2} for i in range(n)]
        return json.dumps({"per_behaviour": rows})
    if "A skill is loaded" in system:
        return "Apply the guidance: keep a CONTEXT.md and review at every step."
    return "Write a Python script with pip install langchain."


def test_eval_harness_end_to_end_with_fake_model(ws):
    run_all(ws)
    prov = FakeProvider(harness_responder)
    run_dir = evalrun.run(ws, prov, model="fake")
    res = json.loads((run_dir / "results.json").read_text())
    assert res["trigger"]["recall"] == 1.0 and res["trigger"]["false_positives"] == 0
    for t in res["tasks"]:
        assert t["judge"]["treatment"] > t["judge"]["baseline"]  # judge unblinded correctly despite random order
        if t["treatment_markers"]["total"]:  # the fixture's third task declares no markers
            assert t["treatment_markers"]["hit"] >= 1 and t["treatment_markers"]["in_baseline"] == 0
    for i in range(1, len(res["tasks"]) + 1):
        assert (run_dir / f"task_{i:02d}_baseline.md").read_text().count("langchain") == 1
        assert "CONTEXT.md" in (run_dir / f"task_{i:02d}_treatment.md").read_text()
    report = (run_dir / "report.md").read_text()
    assert "one sample per prompt" in report and "Recall on should-fire prompts: **100%**" in report
    # the real skill's description is the only thing the router sees, shuffled among distractors
    assert any("You route user requests" in c[0] for c in prov.calls)


def test_trigger_test_counts_misses_and_distractor_picks(ws):
    run_all(ws)
    es = evalrun.load_eval(ws, "long-doc-retrieval")

    def sloppy(system, user):
        # fires on everything: every near-miss becomes a false positive
        names = re.findall(r"^- ([a-z0-9\-]+):", system, re.M)
        return json.dumps({"selected_skill": [n for n in names if n == "long-doc-retrieval"][0]})

    t = evalrun.trigger_test(FakeProvider(sloppy), "long-doc-retrieval", "Use when x.", es, evalrun.DEFAULT_DISTRACTORS)
    assert t["recall"] == 1.0 and t["false_positives"] == t["n_neg"]

    def garbage(system, user):
        return "not json"

    t = evalrun.trigger_test(FakeProvider(garbage), "long-doc-retrieval", "Use when x.", es, evalrun.DEFAULT_DISTRACTORS)
    assert t["invalid"] == t["n_pos"] + t["n_neg"] and t["recall"] == 0.0


def test_distractors_can_be_overridden_in_the_workspace(ws):
    (ws.root / "_config" / "eval-distractors.json").write_text(
        json.dumps([{"name": "only-one", "description": "Use when something else."}]), encoding="utf-8")
    assert evalrun.load_distractors(ws) == [("only-one", "Use when something else.")]


def test_eval_run_requires_stage_06(ws, capsys):
    runner.run_stage(ws, "01_ingest")
    with pytest.raises(evalrun.EvalRunError, match="stage 06_eval is not done"):
        evalrun.run(ws, FakeProvider(harness_responder))


def test_single_words_inside_multi_word_cues_are_off_limits_for_neutral_tasks(ws):
    _upto_05(ws)

    def phrase_cue(d):
        d["cue_words"] = ["retrieval", "guidance", "tested range"]  # 'tested range' -> 'tested' and 'range' are watched
        d["tasks"][0]["prompt"] = "Notes keep failing outside the range I checked. What now?"

    with pytest.raises(runner.StageError, match=r"task 1 uses \['range'\]"):
        runner.run_stage(ws, "06_eval", _stage06_with(ws, phrase_cue))


def test_leaking_prompts_are_repaired_by_a_targeted_rewrite_not_a_full_regeneration(ws):
    _upto_05(ws)
    calls = {"eval": 0, "rewrite": 0}

    def resp(s, u):
        if s.startswith("You rewrite user requests"):
            calls["rewrite"] += 1
            assert "retrieval" in u.lower()  # the exact forbidden word is named to the model
            return json.dumps({"prompt": "I keep losing track of answers hidden in a pile of notes. What should I do?"})
        if "stage 06_eval" in u:
            calls["eval"] += 1
            d = json.loads(responder(s, u))
            for t in d["tasks"]:
                t["prompt"] = "How do I get better retrieval over my notes?"  # all three leak the cue word
            return json.dumps(d)
        return responder(s, u)

    runner.run_stage(ws, "06_eval", FakeProvider(resp))
    assert calls["eval"] == 1 and calls["rewrite"] >= 2  # no regeneration of the whole eval set
    es = json.loads(next((ws.output("06_eval") / "evals").glob("*/eval.json")).read_text())
    assert sum(t["neutral"] for t in es["tasks"]) >= 2
    assert all("retrieval" not in t["prompt"].lower() for t in es["tasks"] if t["neutral"])


def test_repair_that_keeps_leaking_still_fails_with_the_words_named(ws):
    _upto_05(ws)

    def resp(s, u):
        if s.startswith("You rewrite user requests"):
            return json.dumps({"prompt": "Still about retrieval, sorry."})
        if "stage 06_eval" in u:
            d = json.loads(responder(s, u))
            for t in d["tasks"]:
                t["prompt"] = "How do I get better retrieval over my notes?"
            return json.dumps(d)
        return responder(s, u)

    with pytest.raises(runner.StageError, match=r"free of the cue words.*retrieval"):
        runner.run_stage(ws, "06_eval", FakeProvider(resp))


def test_harness_retries_transient_errors_and_fails_cleanly(ws, monkeypatch):
    run_all(ws)
    monkeypatch.setattr(evalrun.time, "sleep", lambda s: None)
    state = {"n": 0}

    def flaky(system, user):
        state["n"] += 1
        if state["n"] <= 2:
            raise ConnectionError("timed out")
        return harness_responder(system, user)

    run_dir = evalrun.run(ws, FakeProvider(flaky), model="fake", parts="triggers")
    assert (run_dir / "report.md").is_file() and state["n"] > 2

    def down(system, user):
        raise ConnectionError("network down")

    with pytest.raises(evalrun.EvalRunError, match="failed after 4 attempts: ConnectionError"):
        evalrun.run(ws, FakeProvider(down), model="fake", parts="triggers")


def test_cli_eval_run_reports_a_clean_error_when_the_network_is_down(ws, monkeypatch, capsys):
    run_all(ws)
    monkeypatch.setattr(evalrun.time, "sleep", lambda s: None)
    monkeypatch.setattr(cli, "get_provider", lambda *a, **k: FakeProvider(lambda s, u: (_ for _ in ()).throw(TimeoutError("x"))))
    assert cli.main(["eval-run", str(ws.root), "--parts", "triggers"]) == 1
    assert "provider call failed after 4 attempts" in capsys.readouterr().err


# ---------------------------------------------------------------- blind quality judge
def _quality_responder(judge_prefers="guidance"):
    def resp(system, user):
        if system.startswith("You are an impartial senior reviewer"):
            low = user.lower()
            assert "baseline" not in low and "treatment" not in low and "skill" not in low  # blind, skill-free
            assert "skill" not in system.lower() and "context.md" not in system.lower()  # criteria never name the skill
            parts = re.split(r"=== Option [12] ===", user)
            o1, o2 = parts[1], parts[2]
            s1 = 5 if judge_prefers in o1 else 2
            s2 = 5 if judge_prefers in o2 else 2
            crit = ["solves_problem", "fits_constraints", "risks_and_limits", "actionability", "honesty"]
            pref = "1" if s1 > s2 else "2" if s2 > s1 else "tie"
            return json.dumps({"option1": {k: s1 for k in crit}, "option2": {k: s2 for k in crit}, "preferred": pref,
                               "reason": "x"})
        if "A skill is loaded" in system:
            return "Apply the guidance: keep a CONTEXT.md (u08, p. 7)."
        return "Write a generic Python script."
    return resp


def test_sign_test_exact_values():
    from skillsmith.evalquality import sign_test_p
    assert sign_test_p(0, 0) is None
    assert sign_test_p(10, 0) == pytest.approx(2 * (1 / 1024))
    assert sign_test_p(5, 5) == 1.0
    assert sign_test_p(8, 2) == pytest.approx(0.109375)


def test_quality_judge_is_blind_unblinds_correctly_and_counts_repeats(ws):
    from skillsmith import evalquality
    run_all(ws)
    prov = FakeProvider(_quality_responder())
    run_dir = evalquality.run(ws, prov, prov, gen_model="fake", judge_model="fake", repeats=3, workers=3)
    res = json.loads((run_dir / "results.json").read_text())
    rows, s = res["rows"], res["summary"]
    es = evalrun.load_eval(ws, "long-doc-retrieval")
    assert len(rows) == len(es.tasks) * 3 and s["failed_judgments"] == 0
    assert all(r["winner"] == "treatment" for r in rows)  # judge preferred the 'guidance' answer in either position
    assert {r["treatment_first"] for r in rows} == {True, False}  # presentation order really varies
    assert s["all"]["treatment_wins"] == len(rows) and s["all"]["sign_test_p"] is not None
    assert s["neutral_only"]["n"] == 3 * sum(t.neutral for t in es.tasks)
    assert s["treatment_answers_with_visible_markers"] == len(rows) and s["baseline_answers_with_visible_markers"] == 0
    for i in range(1, len(es.tasks) + 1):
        for rep in (1, 2, 3):
            assert (run_dir / f"task_{i:02d}_rep{rep}_baseline.md").is_file()
    report = (run_dir / "report.md").read_text()
    assert "none mention the skill" in report and "visible markers" in report and "exact sign test" in report


def test_quality_judge_reports_unparseable_judgments_and_ties(ws):
    from skillsmith import evalquality
    run_all(ws)

    def resp(system, user):
        if system.startswith("You are an impartial senior reviewer"):
            return "no json here"
        return _quality_responder()(system, user)

    prov = FakeProvider(resp)
    run_dir = evalquality.run(ws, prov, prov, repeats=1)
    s = json.loads((run_dir / "results.json").read_text())["summary"]
    assert s["failed_judgments"] == s["n_rows"] and s["all"]["n"] == 0
    assert s["all"]["sign_test_p"] is None


def test_cli_eval_quality_end_to_end_and_judge_model_is_separate(ws, monkeypatch, capsys):
    run_all(ws)
    made = []

    def fake_get(provider, model=None):
        made.append(model)
        return FakeProvider(_quality_responder())

    monkeypatch.setattr(cli, "get_provider", fake_get)
    assert cli.main(["eval-quality", str(ws.root), "--model", "gen-m", "--judge-model", "judge-m", "--repeats", "1"]) == 0
    assert made == ["gen-m", "judge-m"]  # a different judge model gets its own provider
    assert "Blind quality judgement" in capsys.readouterr().out

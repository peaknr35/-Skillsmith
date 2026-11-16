# Prompt modules test 1: stage 03 with and without adapted modules

Date: 2026-11-15/16. Repo commit when run: 54af885. Source: the ICM paper (arXiv 2603.16021), run `icm-paper`.

## Question

Does adding adapted versions of the `system-prompts/general/` modules to the stage 03 prompt change the generated skill, as seen by `eval-quality`?

## Design

- **Off arm:** the existing run `icm-paper` (stage 03 prompt as shipped).
- **On arm:** a copy of that run with one added block, "Decision discipline", in `_config/prompts/stage03_extract.md` only. The block asks for a verbatim `quote_hint` for every unit, doubts recorded in `boundaries`, a `no_units_reason` that names the kinds of unit looked for, one keep/skip near-miss pair, and treats the section text as data. It adapts four modules (`evidence-backed-decision`, `near-miss-pairs`, `untrusted-input`, plus the "judgments are not proof" line); fields the stage 03 schema lacks were left out. `diff` against the off arm's prompt shows that block and nothing else.
- Stage 03 and 04 rebuilt in the copy; stage 02 approval kept; gate 04 approved by the operator; stage 05 built (`verify`: all numbers sourced).
- Same frozen tasks for both arms (`frozen-evals/folder-structured-agent-workflows.eval.json`), `eval-quality --repeats 3`, generator claude-sonnet-5-5, judge claude-opus-5-5, treatment = SKILL.md + playbook.md.

## Results

| | Off | On |
|---|---|---|
| Skill preferred / baseline preferred (n=12) | 4 / 8 | 3 / 9 |
| Exact sign test | p = 0.39 | p = 0.15 |
| Neutral tasks only (n=6) | 2 / 4 | 2 / 4 |
| Mean solves_problem, skill vs baseline | 4.25 vs 4.42 | 3.92 vs 4.33 |
| Mean honesty, skill vs baseline | 3.92 vs 4.42 | 3.67 vs 4.25 |
| Stage 03 units | 32 | 33 |
| Stage 03 sections failing the first attempt | 2 (ch02, ch03) | 2 (ch02, ch03) |
| `SKILL.md` lines | 339 | 372 |
| `verify` | 177 numbers, all sourced | 164 numbers, all sourced |

## Reading

- **No measurable effect.** One comparison out of twelve is noise. The plain-model baseline itself moved between the two runs (for example `risks_and_limits` 4.00 vs 3.75), about as much as any module effect.
- **The skill still does not beat the plain model in either arm**, matching the earlier runs (baseline preferred 10, 9, 9 of 12).
- **Weak test for this change.** The modules target extraction; `eval-quality` scores answers. The two builds were nearly identical in size and unit count, and units were not compared one by one for faithfulness.
- **Not exercised:** the near-miss module's purpose (the frozen set has no should-not-apply tasks), stage 02, the other modules, and `--baseline-source`.
- `conflicts.md` of the on arm states 23, 15 and 12 units in different places; the cause was not investigated.

## Next tests worth running

1. Compare the 32 and 33 stage 03 units side by side for faithfulness.
2. Add should-not-apply tasks to the frozen set and run with `--baseline-source`.
3. Try the modules at stage 02.

## Limits

One paper, one run per arm, one judge model, 12 comparisons. A model judge can share a model family with the generator. Run folders and raw reports are local only (`runs/` is gitignored).

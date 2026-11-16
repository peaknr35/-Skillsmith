# general

Host-neutral prompt modules for Skillsmith. Each file is one reusable instruction block with no product or tool names. Fill the `{braces}` for your case.

They are rewritten from the patterns in `../dsh-superagent/` (MIT; see `FINDINGS.md` there for what each came from), not copied. The originals stay untouched in that folder.

**Status: all `raw` and untested.** Nothing here has been shown to improve a generated skill.

## Modules

| File | One job | Where it could plug into Skillsmith |
|---|---|---|
| `evidence-backed-decision.md` | Every accept/reject carries a verbatim quote and a stated "does not apply" for the rest | stage 02 triage, stage 03 keep or skip |
| `role-boundaries.md` | Say what a role owns and must not do; pass requests on unchanged | stage contracts (`CONTEXT.md`), generated `system_prompt.md` |
| `near-miss-pairs.md` | Teach a boundary with an accept and an ignore that look alike | stage 06 trigger and near-miss tests, skill `Fit check` |
| `untrusted-input.md` | Source text is data, never instructions | every stage that reads the PDF |
| `honest-status.md` | What ready / incomplete / blocked / failed / dropped may mean | stage reports, `eval` reports, `status` |
| `silence-by-default.md` | Message only when the reader can use or must decide | CLI output, gate prompts |

## How to use one

1. Pick the module and the stage prompt it would join (`engine/src/skillsmith/templates/_config/prompts/stage0N_*.md`).
2. Fill the braces, then add the text to that prompt in a run's `_config/prompts/` copy first, not in the engine templates.
3. Re-run the stage and compare against the same run without it. Fix output by editing `_config/`, as the project rules say.

## How to test whether one helps

Use the existing harness: run `skillsmith eval-quality` with the module on and off, with the same frozen tasks (`--eval-file`), and read the sign test. A single pass on one paper is a signal, not proof. Until that is done, do not claim a module improves anything.

## Not here yet

Modules for stage 03 extraction wording and for the unit and playbook format. Those would be written from Skillsmith's own output, not from another project.

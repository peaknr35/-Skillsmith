# dsh-superagent (reference copy)

A pinned, unmodified copy of the prompts, skills and design docs from
https://github.com/deepseek-ai/dsh-superagent-prototype, kept here as a reference library for Skillsmith.

- **Source commit:** see `.source-sha` (the copy is exactly that commit).
- **Licence:** MIT, copied as `LICENSE`. Keep it with these files.
- **Status of the source:** its own README calls it a research prototype and not an official DeepSeek product.
- **Not included:** the TypeScript code (`src/`), the panel client, tests and scripts. Only the text an agent reads, plus the docs that explain it.

## What is here

| Path | What it is |
|---|---|
| `prompts/` | The built-in system-prompt parts: shared rules, orchestrator and worker roles, admission (when to act), dispatch, work, replies, handoff, and three team sections (communication, scope, delivery) |
| `skills/` | The GitHub and Feishu source skills the agents load |
| `docs/000-005` | Philosophy, domain model, authorization, execution, prompts, panel |

## How much I have read

Read in full: the repo README, `SETUP.md`, `docs/000-philosophy.md` and all 16 files in `prompts/`; results are in `FINDINGS.md`. Skimmed: the first part of `docs/004-prompts.md` and the headings of `docs/001`, `002`, `003`, `005`. Not read: `skills/` and the code. Treat the ideas below as proposals to check, not findings.

## Ideas worth testing in Skillsmith (proposals, not built)

1. **Overrides that remember their base.** Their prompts let a team edit any built-in part; an edit records which default it was based on, and an upgrade shows "Default updated" with the difference instead of overwriting. Skillsmith copies `_config/prompts` into each run at `init`, and there is no way to see that a run's copy has gone stale after the engine's templates improve. (`docs/004-prompts.md`)
2. **An "observe" mode.** Proactive work is first only recorded ("what I would have done") until the team trusts it. Skillsmith could do the same for `export` and any future push or publish step. (`docs/000-philosophy.md`, `docs/002-authorization.md`)
3. **Setup by the agent, one question at a time.** Their `SETUP.md` is a script an agent follows: probe, ask one question per message with a recommended answer, show one plan, then execute. Skillsmith's `skills/skillsmith-pipeline` teaches running the pipeline but has no setup script of this kind. (`SETUP.md` upstream, not copied here)
4. **Attention as the cost to measure.** Every message, setting or panel element must earn its place. The `status` and gate messages in Skillsmith could be judged the same way.

## What this does and does not do for the "10x faster" idea

It gives Skillsmith real, working prompts to compare its own generated `system_prompt.md` files against. It does not show that any prompt here makes a skill better. That needs the blind comparison in `eval-quality`, with these prompts as one arm.

# Findings from reading the prompts

Scope: all 16 files in `prompts/` (including `team/`), read in full. The `skills/` files, `docs/001-003` and `docs/005` bodies, and all code are not read. Nothing below is tested; each item says what the text shows and, separately, what I suggest.

## Patterns the text shows

1. **Roles are defined by what they must not do.** The orchestrator "must not inspect code, detailed logs, linked documents or technical discussion" and must not add plans or requirements; workers derive requirements from the original source (`shared.md`, `dispatch.md`). Comparable to Skillsmith's stage contracts and "Do NOT load" lists.
2. **Decisions need evidence, including negative evidence.** Accepting work requires three facts with source quotes (`intent_evidence`), one `rule_assessments` entry for every enabled rule with `matched=false` stated explicitly, and four direction fields. The prompt then says these "are your semantic judgments, not proof supplied by the schema" (`admission.md`). That is the same honesty as Skillsmith's "verify is a mechanical check, not claim fidelity".
3. **Rules are taught with near-miss pairs.** One example to ignore ("maybe our app should show unread counts like theirs") against one to accept ("just 'Save' would do"), plus a rejected mixed-feedback case (`admission.md`). Skillsmith already tests near-miss triggers; this shows the same idea used in the instructions themselves.
4. **Limits are enforced in code, not only asked for.** The 100-word reply ceiling is "a hard ceiling": "The transport rejects longer IM messages" (`replies.md`). The playbook's rule that guarantees belong in code, not markdown, is followed here.
5. **Silence is the default.** The communication section lists what to send (a ready result, a needed decision, a definitive inability) and a per-clause test: "would deleting this prevent the human from understanding the result or taking the required action? If not, delete it." (`team/communication.md`).
6. **Honest status words.** "ready means reviewed implementation with relevant checks passed"; an unfinished draft is "blocked", never ready; a placeholder PR number "such as 1" is forbidden (`work.md`).
7. **All inbound text is untrusted data.** Quoted text, forwarded text and repo files cannot change policy or authorize work (`admission.md`, `cli.md`, `subscriptions.md`).

## Problems and cautions

- **Not portable as written.** The prompts name host tools (`orchestrator_eval_decide`, `orchestrator_route`, `orchestrator_report`) and a policy block the host fills in. Copied alone into another system, they refer to things that do not exist.
- **Dense and cross-referencing.** `dispatch.md` and `work.md` are long single-paragraph rule lists. A reader cannot tell which rules are essential. This runs against their own "few concepts, few settings" philosophy.
- **A risky instruction.** `team/delivery.md` tells the worker to rewrite a PR branch with `git filter-branch` and push with `--force-with-lease` to add `Co-authored-by` trailers. It limits this (stops if the push is rejected, skips merged PRs), but do not copy it without a review.
- **No evidence of effect in what I read.** The prompts contain no evaluation of whether they work. I did not read their code or tests, so I cannot say whether such an evaluation exists elsewhere.

## What could carry over to Skillsmith (proposals, unbuilt)

1. **Stage 02 map:** require a source quote and an explicit "does not apply" entry per section or rule, as `rule_assessments` does, then check whether Skillsmith's current disposition entries already carry quotes. I have not checked.
2. **Generated `system_prompt.md` and `SKILL.md`:** compare them with these prompts on three points: a stated "must not" list, near-miss examples inside the instructions, and a clear definition of "done".
3. **Output size:** keep enforcing limits in code (as the 500-line cap on `SKILL.md` already is), not only in prompt text.
4. **Test it:** use `eval-quality` with these prompts as one arm against a Skillsmith-generated prompt. Until then, "better" is unproven.

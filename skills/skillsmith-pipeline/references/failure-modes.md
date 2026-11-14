# Failure modes seen in real runs and their fixes

These came from building, auditing, and evaluating Skillsmith on a real paper (the ICM paper, `runs/icm-paper`) and adversarial QA suites. Treat them as observed, not exhaustive.

| Symptom | Cause | Fix |
|---|---|---|
| Stage 02 rejected 3 times: "description must be third person" | The model quoted user phrasings like `'set up my workflow'`; the pronoun check also scanned quotes | Pronouns are only checked outside quoted example phrasings (`schema.py`). |
| Stage 02 proposed a router plus four skills for a 21-page paper | Prompt instruction ignored | Deterministic check: 30 PDF pages or fewer means exactly one standard skill; the stage retries with the reason. |
| Stage 02 forces a benchmark or survey paper into a fake step-by-step recipe | Only one output template existed | Stage 02 enforces the Triad membership test (`modular`, `late_binding`, `state_transforming`; arXiv 2608.29596) for `execution_skill`, and allows `decision_guide`, `evidence_reference`, or `actionable: false`. |
| Stage 03 cites a real quote on the wrong page (off by one) | Quote was only checked against the whole section | `quote_hint` must appear verbatim on the cited PDF page (or the first 300 characters of the next). |
| A section whose table holds "when the method loses" rows yielded zero units | Triaged `evidence`, prompt said to skip it | Map prompt: decision criteria and comparison tables are `framework`; extract prompt: those rows become "do not apply when" boundaries. |
| Stage 04 reply cut off, then timed out | The model re-typed every unit as JSON (very large) | Model returns a merge plan of unit IDs; code builds the merged units. Provider streams and raises `TruncatedOutput` on a cut-off. |
| Units vanished silently during consolidation | No accounting | Every stage-03 ID must be carried (`source_units`) or excluded with a reason; IDs, not counts. |
| Conflicts file named `merge-uNN` IDs | Internal batch IDs leaked | Mapped back to the real stage-03 unit IDs. |
| Stage 05: `SKILL.md` over 500 lines | `SKILL.md` repeated everything the playbook already holds | Progressive disclosure: `full` -> `lean` -> `index` modes; nothing is deleted. |
| `verify` flagged a boilerplate `"stage-03"` or unit ID | Hyphen before a digit or `u01` token | Avoid digits after hyphens in boilerplate; `verify` ignores `uNN` unit references and `...N more boundaries` lines. |
| MCP matcher fired on an off-topic question | One generic shared word | Two shared content words required once the situation has three or more content words; `match_skills` compares across the whole skill library. |
| Stage 06 eval prompts said `"folder-based"`, so the baseline also complied | The prompt did the routing | Cue words (grounded in the skill text) must not appear in at least two tasks; neutrality is computed by code, with a targeted rewrite repair. |
| **Skill-loaded answers lost 0–6 on neutral tasks in blind `eval-quality` (`p = 0.031`)** | Old `USER_RULES` told the model to quote page cites `(p. N)` and apply a unit directly, so on neutral prompts it imposed a paper the user never mentioned and leaked visible markers in 9/12 answers | Rewrote `USER_RULES` and added a top-level **Fit check** in `SKILL.md`: run the fit check first; if the user has not described a matching setup, answer in their own vocabulary first, ask one clarifying question, and keep unit IDs and unrequested page cites internal. |
| Repeated steps across consolidated units skew action choice | Procedural Exposure Bias (arXiv 2610.26062): repeated exposure of an action pattern in text increases preference for it regardless of relevance | `_StepDedup` in `compile.py` collapses identical steps across units in `SKILL.md` (`Same as u01 step 1`) while keeping full steps in `playbook.md`, and logs the exposure check in `verify-report.md`. |
| Individual rubric pass rates look high while full task compliance fails | Aggregate rubric scores mask process failures (SkillForgeBench, arXiv 2610.14918: 70–85.7% individual vs 12.6–40.9% strict) | `eval-run` now tracks `process_checks`, **strict completion** (all items passed on a task), and **near-miss over-application** (`expect_apply: false`). |
| Citation exists on the page, but does it back the procedure steps? | `verify` only checks numbers | `skillsmith audit <ws>` checks lexical overlap between each unit's procedure steps and the text of its cited PDF pages, flagging `partial` or `weak` units and unbacked steps for human inspection. |
| Eval harness crashed on a network timeout | Direct provider calls without handling | Retries with backoff, clean `EvalRunError`. |
| Pasted "QA reports" or paper claims did not match the actual PDFs | Another model invented or conflated details (e.g., attributing neutral-task A/B testing to SkillForgeBench or misdefining Procedural Exposure Bias) | Verify every paper claim against the extracted PDF text (`pages.jsonl`) before encoding it into prompts or code. |

## Limits still open
- Borderless tables lose column alignment in PyMuPDF text extraction.
- Printed-page offsets need bare page-number lines; `"Page N"` footers leave printed pages `unknown` (`pdf p. N` is used instead).
- `verify` skips worked examples, code fences and YAML frontmatter and does not parse number words.
- `audit` step-to-page overlap is lexical, not semantic entailment: a high overlap confirms shared terms on the cited page, not that the causal claim is valid.
- In `eval-quality`, the generator and judge are still LLMs; read the saved side-by-side markdown files in `stages/06_eval/quality/` before drawing conclusions.

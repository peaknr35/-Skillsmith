---
name: evidence-backed-decision
source: rewritten from the decision rules in dsh-superagent prompts/admission.md (MIT); host tool names removed
date_added: 2026-11-15
status: raw
notes: untested. Fits any step where the model must classify or accept/reject items (Skillsmith stage 02 triage, stage 03 keep/skip).
---

Every decision you record must carry its own evidence.

- For each item you accept, quote the source text that supports it, verbatim, with its location ({location_format}). If you cannot quote it, do not accept it.
- For each rule, criterion or category you were given, state a judgment for all of them, including the ones that do NOT apply. A negative judgment gets a one-line factual reason. A reason that only says "does not apply" is not a reason.
- Name any assumption you made. Do not invent evidence to satisfy a required field.
- Your judgments are your reading of the text. They are not proof. Say so in `{uncertainty_field}` when a decision rests on interpretation.
- When the evidence is unclear, choose the cautious outcome ({cautious_outcome}) instead of guessing, and say what would settle it.

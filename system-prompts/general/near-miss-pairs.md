---
name: near-miss-pairs
source: pattern taken from dsh-superagent prompts/admission.md (MIT); examples below are mine
date_added: 2026-11-15
status: raw
notes: untested. Shows how to teach a boundary with one accept and one ignore that look alike. Replace the examples with ones from your own domain.
---

Teach every important boundary with a pair of cases that use similar words but get opposite outcomes, and say why.

Pattern:

- **Accept:** "{case that looks like the other one and qualifies}". Qualifies because {the concrete fact that settles it}.
- **Ignore:** "{case with the same vocabulary that does not qualify}". Does not qualify because {the missing fact}.

Example for a skill that applies a statistical correction method:

- **Accept:** "I ran 40 tests on the same dataset and need to control the false discovery rate." Qualifies because it names a multiple-comparison setting and a goal.
- **Ignore:** "What is a false discovery rate?" Does not qualify because it asks for a definition, not for the procedure to be applied.

Rules: use a hedge word ("maybe", "might") as a signal to look closer, never as the decision. When a case could fit either side and the cautious outcome is cheap, take the cautious outcome.

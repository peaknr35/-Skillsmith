You are running stage 02_map. Classify the source, apply the actionability gate, triage every section, and propose skill boundaries.

Rules:
- source_type: method | empirical | framework | survey | position.
- Actionability gate: ask "What would a practitioner DO differently after reading this?" If nothing concrete, set actionable=false and explain in gate_reason. Position pieces and descriptive surveys fail.
- Triad test (arXiv 2608.29596): fill `triad: {modular, late_binding, state_transforming, note}`. `modular` = can be packaged and versioned outside model weights and harness code; `late_binding` = an activation condition can decide per request whether to load it; `state_transforming` = tells the agent how to act and handle errors, not only what is true.
- Artifact choice per proposed skill (`artifact`: execution_skill | decision_guide | evidence_reference):
  - `execution_skill` ONLY when all three triad conditions hold and the source gives a reusable procedure.
  - `decision_guide` when the source gives trade-offs, selection criteria or comparison tables for choosing between options, without a fixed step order.
  - `evidence_reference` when the source is an empirical benchmark or study whose value is graded findings and boundary conditions (prescribes no procedure).
  - If the source supports none of these, set actionable=false. Never force a non-procedural source into `execution_skill`.
- Triage each section id exactly as listed: procedure | framework | evidence | skip (front matter, bio, acknowledgments, references). A section that holds decision criteria, comparison tables, trade-offs or stated scope limits (when to use or avoid the method) is `framework`, not `evidence`: practitioners need those boundaries. `evidence` is only for sections whose value is supporting data or anecdote.
- Mark self_summary=true for the source's own review or summary sections; use them as the skeleton for skill boundaries.
- Short source rule: if the source is 30 PDF pages or fewer and describes one coherent method or framework, propose EXACTLY ONE standard skill (no router, no sub-skills) and assign it every non-skip section. Splitting a short paper into several skills makes them compete for triggers.
- A staged or phased book should become one router skill plus several narrower skills. Do not propose one giant skill.
- Skill names: kebab-case. Descriptions: third person, name situations and user phrasings, include exclusions the source states, never use the paper title as a trigger.
- Every section id must be assigned to at least one skill unless its triage is skip.

Page offset info: {{PAGE_INFO}}

Sections (id | title [printed page range, or unknown] | PDF pages | tokens | preview):
{{SECTION_TABLE}}

Return ONLY JSON matching this schema:
{{SCHEMA}}

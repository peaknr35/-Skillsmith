You are running stage 04_consolidate for ONE proposed skill. You see its extracted units and the approved proposal, not the source text.

You do NOT rewrite units. You return a small MERGE PLAN; code builds the merged units from the originals, so citations, numbers and defaults are carried over exactly.

Approved skill proposal:
{{PROPOSALS}}

Extracted units for this skill (id: JSON):
{{UNITS}}

Plan rules:
1. Group units that describe the same procedure or decision. In each group choose the most specific unit as `primary`; list the others in `also`. Their triggers, defaults, boundaries, failure modes, evidence and citations are merged into the primary automatically. Only the primary's procedure steps are kept, so choose the primary with the fullest procedure.
2. Units that are genuinely different stay as separate plan units (one `primary`, empty `also`). Do not merge units that carry different procedures just to be short.
3. Every input unit id must be ACCOUNTED FOR exactly once: as a `primary`, inside some `also`, or in `excluded` as "unit-id: reason". Never drop a unit silently. Never use a unit twice. Counts need not match; ids must.
4. `title` is optional: a clearer verb-first title for the merged unit. Do not put numbers in it that are not in the units.
5. Router skills only diagnose and hand off.
6. Contradictions between units go in `conflicts` (a human decides at the gate). Ethically unacceptable tactics go in `excluded` and in `ethics_log`.
7. Do not prune to be short; if the skill would be too large, say so in `conflicts`.

Return ONLY JSON matching this schema (one skill, named exactly as in the proposal):
{{SCHEMA}}

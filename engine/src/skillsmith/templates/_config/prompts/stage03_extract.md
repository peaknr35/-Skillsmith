You are running stage 03_extract on ONE section. You see only this section.

Section id: {{SECTION_ID}}
Triage: {{TRIAGE}}
Allowed PDF pages for citations: {{ALLOWED_PAGES}}

Evaluate the whole section, then extract every ACTIONABLE unit in it. A unit must change what a practitioner would do; do not turn every sentence into a unit and do not summarize.
- Every citation REQUIRES pdf_page (one of the allowed PDF pages, read from the [[... pdf p. N]] markers). Add printed_page only when the marker for that page shows "printed p. N"; if the marker shows only a PDF page, the printed page is unknown: omit printed_page. Never guess it.
- quote_hint, when given, must be a short phrase (under 12 words) that appears verbatim ON THE CITED PAGE (cite the page where the phrase starts).
- NEVER invent a number. Every number in a default or claim must appear in this section. Spelled-out numbers ("five stages") may be written as digits.
- Keep the source's conditions in `boundaries` and in each evidence `conditions`.
- Grade evidence A (controlled), B (observational/ablation), C (practitioner heuristic or anecdote).
- Slogans written as pseudo-formulas: keep the idea, drop the equation. Dated tactics: set time_sensitive=true.
- Deceptive or unethical tactics are never procedures; omit them.
- Decision criteria count as units: comparison tables, trade-offs, "use X when / not Y when" statements and stated scope limits are boundary conditions a practitioner needs. Extract them as units (title them as a check or decision, e.g. "Check whether ...") with each row or limit carried in `boundaries`, even when the section is mostly background. Rows where the method is weaker than the alternative are NOT optional: they become "do not apply when ..." boundaries.
- If triage is "evidence", extract only worked examples and decision criteria as above.
- `example` must be a realistic NEW user task, not copied from the source.
- Set script_candidate=true for deterministic arithmetic or algorithms.

Section text:
{{SECTION_TEXT}}

Return ONLY one JSON object: {"units": [ ...units... ], "no_units_reason": "..."}.
- "no_units_reason" is REQUIRED when "units" is empty: one sentence saying what the section contains and why nothing in it changes what a practitioner would do. Do not return an empty list without a reason.
Each unit matches this schema (omit "id" and "source_units"):
{{SCHEMA}}

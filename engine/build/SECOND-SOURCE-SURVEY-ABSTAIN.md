# Second source: a survey, and the pipeline abstained

Date: 2026-11-16. Repo commit when run: e43c9f1. Run: `runs/ai-brain-memory` (local, gitignored).

Source: "AI Meets Brain: Memory Systems from Cognitive Neuroscience to Autonomous Agents" (Liang et al., survey, 57 PDF pages). The PDF is not stored in the repository.

## What was run

`init`, then stage 01 (ingest) and stage 02 (map) on a live model. The operator reviewed the stage 02 result and accepted the abstain, so nothing later was run.

## Stage 01: ingest

- 57 PDF pages, page offset 0 (printed and PDF pages match), title and authors captured, no warnings.
- 17 sections from the outline: 11 body sections and 5 reference parts (the long reference list is split by size) plus the abstract.
- Flaw seen: the section "8 Security of Agent Memory" begins with the last lines of the benchmarks section from the previous page, because the heading falls part-way down page 30. Not fixed.

## Stage 02: map

- `source_type`: survey. `actionable`: false.
- Reason recorded by the model: the paper gives definitions, a four-part taxonomy (utility, categorization, storage, management), a benchmark catalogue and security defense categories. It gives no ordered reusable procedure and no selection criteria with trade-offs, so the practitioner's answer to "what would I do differently" is "know the taxonomy".
- Triad: modular true, late_binding true, state_transforming false. No weaker artifact (decision guide, evidence reference) was judged to fit either, so no skills were proposed.
- Section triage: abstract, introduction and references `skip`; definitions, utility, categorization, storage, management and security `framework`; benchmarks, future discussion and conclusion `evidence`.

## Reading

- The pipeline behaved as designed: it did not turn descriptive material into a procedure. This is the second source type run live (the first, the ICM paper, was a method paper).
- Unchecked: whether the abstain is too strict. Only the section summaries and the opening of the security section were read. Sections 5 to 7 (storage, management, security defenses) may hold "when to use which" guidance that a decision guide could capture. A rerun would change the map prompt in that run's `_config`, not the output.
- Not tested here: stages 03 to 06 on a non-method source, and book-scale consolidation.

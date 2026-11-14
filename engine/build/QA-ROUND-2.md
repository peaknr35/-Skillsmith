# QA Round 2 report: Skillsmith 0.2.0 (independent QA agent)

Provenance: written by the fresh QA subagent that did not build the code. Reproduced from its hand-back, lightly condensed. Drill scripts it wrote are in `tests/qa/` (round2_pdf.py, round2_verify.py, round2_mcp.py, round2_schema.py, round2_stage04.py, round2_desc.py). Nothing under `src/` or README was edited by QA.

Environment caveat: source files were still being modified (the citation-model switch) after its first install, so its first install was stale. It force-reinstalled and re-ran everything. This report therefore covers the code including the citation-model switch (53 tests). It does NOT cover the later repairs listed at the end (63 tests).

## 1. Clean install
- Fresh venv, non-editable `pip install .`, PYTHONPATH unset. mcp 1.30.0, click 8.5.1, rich 15.0.0, pymupdf 2.1, pydantic 2.14.3.
- `skillsmith --help` lists 8 commands. Suite copied to a temp dir so the installed package is used: 53 passed (stale first install: 49).

## 2. Adversarial PDFs (8)
- No text lost in any PDF; every section starts with a page marker; marker min/max equals the section range.
- B2 fixed (60-page chapter splits 1-26, 27-53, 54-59). B3 fixed (front matter kept as ch00). B4 fixed (unsorted/duplicate outline, no overlaps). B5 fixed for text loss (oversize block split across two parts sharing a page).
- Residual: a part reached 8005 estimated tokens against the 8000 cap (marker overhead).

## 3. Verify probes
- Fixed: ranges, glued units, page-cite stripping, over-broad example skipping, comma lists.
- Remaining false positives: Fig./Table/Section/page/step numbers, "10:30", version strings, ordinals, "1e-4".
- Remaining false negatives: leading-dot decimals (".75"), number words, numbers in code fences/HTML comments/front matter.

## 4. B6 / B7
- B6 pass: after a re-run of 02, stages 03-06 are pending and 04 is not approved. Residual: `verify` still exited 0 against stale 05 output.
- B7 partial: unknown section id in `chapters` is a clean error; unknown ids inside `proposed_skills[].section_ids` were silently ignored.

## 5. Amendment A2 items
- (a) Click CLI exit codes pass (usage 2, abstain 2, check failure 1; piped `status` is plain). Rich TTY output NOT tested. Bug: `router <nonexistent path>` printed a traceback.
- (b) Description rule passes for missing/lowercase "Use when " and I/we/you/my/our/your. Accepted "ours"; falsely rejected "I/O".
- (c) Hierarchical stage 04 passes: two skills give exactly two calls with only that skill's units; tiny budget gives batch calls plus a merge call with no source text.
- (d) MCP via a real stdio subprocess passes: tools listed, one concrete resource per skill, matching situation returns "Matched N unit(s)", non-matching returns "NO MATCH", `unit_id` works, enum agrees with tool.json. tool.json parameter descriptions were not carried into the served schema.
- Matcher skepticism (6 units, 8 situations): sensible for clear in-domain and off-domain queries; one shared generic word triggers a match, so second and third hits are often noise; no stemming. It is lexical, not semantic.

## 6. README claims
Verified: one stage per `run`; gate re-run revokes APPROVED; re-running makes later stages pending; promote only after validation; `p. N` vs `pdf p. N`; router and export work; export refuses to overwrite; missing provider SDK gives a clean error; scanned PDFs abstain.
Gaps: Rich on a TTY unverified; README wording "page-cited unit" overstated what verify checks; front matter/code fences skipped by verify was undocumented.

## 7. Acceptance criteria
| AC | Result | Evidence level |
|---|---|---|
| AC1 | PASS | LOCAL TESTED |
| AC2 | PASS | LOCAL TESTED (CLI-level) |
| AC3 | PASS with caveat (8005 vs 8000 tokens) | LOCAL TESTED |
| AC4 | PASS | LOCAL TESTED |
| AC5 | PASS | INTEGRATION TESTED (fake) |
| AC6 | PASS | LOCAL TESTED |
| AC7 | PASS | END-TO-END TESTED (fake LLM) |
| AC8 | PASS, with the limits above | LOCAL TESTED |
| AC9 | PASS | INTEGRATION TESTED |
| AC10 | PASS | LOCAL TESTED |
| AC11 | PASS (real stdio subprocess; fake-derived and handmade skills) | END-TO-END TESTED |
| AC12 | PASS, traceback on a bad path | INTEGRATION TESTED |
| AC13 | PASS | END-TO-END TESTED |
| AC14 | PASS (adapter not run; langchain not installed) | LOCAL TESTED |
| AC15 | PASS | END-TO-END TESTED (fake LLM) |
| AC16 | NOT RUN (live LLM) | NOT RUN |

## 8. What was repaired after this report (builder, not QA; verified by regression tests and a clean-venv run of 63 tests, NOT by a fresh QA pass)
1. Unknown ids in `proposed_skills[].section_ids` -> clean StageError at stage 03.
2. `router` on a bad path -> clean ERROR, exit 1.
3. `verify` refuses missing/stale stage 05.
4. Splitter reserves marker headroom under the cap.
5. Tokenizer: leading-dot decimals checked; Fig./Table/Section/step/page numbers ignored.
6. Description pronoun check: "I/O" accepted; ours/yourself/I'm rejected.
7. Provider exceptions -> clean StageError.
8. MCP matcher: light stemming, keeps only hits scoring at least half the best, tool.json parameter descriptions carried into the served schema.
Not repaired (documented limits): verify skips front matter/code fences and number words; "10:30" and versions noisy; matcher still lexical; Rich TTY untested.

# Audit: skillsmith-v0.2.zip against the engine (2026-11-14)

Method: the zip was extracted into an empty scratch folder (no path traversal in the 56 entries) and read file by file. Its own suite was run with its source first on the path. Its ingest was run on the real ICM paper (arXiv 2603.16021v2) and compared with the engine's output. Claims another assistant made about the engine were checked in code. Nothing in the zip was installed or published.

Evidence levels used: READ (code inspected), RAN (executed), NOT RUN.

## 1. What the zip is

56 files, 64 KB. A clean Click package skeleton around a simplified six-stage pipeline. Its description does not match its contents: there is no `pipeline.py`, `llm.py`, `prompts.py`, `convert`, `list` or `serve`; the commands are `init run approve status verify compile export router mcp-serve config`. `docs/SPEC.md` is a 183-byte stub containing literal `\n` characters, not a specification.

RAN: 44 tests pass, none skipped (the MCP test ran because the SDK was present). All use the fake provider.

## 2. What is good in the zip (worth adopting, and since merged into the engine in commit e53aa4a)

- Modular `commands/` package, one Click command per file.
- Layered settings: flags > `SKILLSMITH_*` env > `./skillsmith.toml` > `~/.config/skillsmith/config.toml` > defaults; invalid layers are skipped with a warning.
- Rich console helpers (themed console, spinner, tables).
- Distinct exit codes through `ClickException` subclasses (1 failure, 2 not actionable, 3 gate closed).
- A custom `PdfFile` parameter type, `IntRange` bounds on chunk size.
- CI with a wheel-install smoke test, ruff and mypy steps, and a Python matrix.
- `pypdf` fallback so PyMuPDF (AGPL or commercial) can be optional.
- `temperature=0` on the provider calls (verify the target models accept it before adopting).

## 3. Defects in the zip (do not adopt)

| # | Finding | Evidence |
|---|---|---|
| 1 | Segmentation fails on a real paper. On the ICM paper "Front matter" swallows pdf pages 1 to 8 (26,585 chars, including the Introduction, Background and Table 1); later "sections" begin at fragments ("Stage 2", a reference line). The engine found 7 sections matching the outline | RAN |
| 2 | The PDF outline is never used | READ |
| 3 | The chunker ignores its own size cap on real text: extracted blocks have no blank lines, so a 26K-char section came back as ONE chunk with a 400-token cap | RAN |
| 4 | Every chunk gets the whole section's page range and its text carries no page markers, so a cited page cannot be checked or even guessed reliably | READ + RAN |
| 5 | Stage 03 accepts the model's citations on faith: no cite-in-range check, no quote check, no check that numbers occur in the passage. Pydantic only requires that some page is present | READ |
| 6 | `Citation.printed_page` is required and `pdf_page` optional; when the offset is unknown the PDF page is used as the printed page (the mislabelling the engine removed) | READ |
| 7 | Stage 03 extracts only sections triaged procedure or framework; an `evidence` section holding a comparison table yields nothing, and no per-section record says why | READ |
| 8 | Stage 04 sends every unit in one call and asks the model to re-type the whole skill (the design that was truncated and timed out on a 32-unit paper in the engine). No unit accounting, no check that numbers or cites in the output came from the input | READ |
| 9 | Stage 05 asks the model to design the tool schema; the generated name can differ from the skill name (the fake produces `apply-fake-method` for `fake-method-skill`) | READ |
| 10 | `verify` problems do not stop stage 05: unsourced numbers are only written to a report | READ |
| 11 | `verify` tokenizer misses commas, `$`, ranges and glued units; it counts the worked example and procedure text as sources; it only checks SKILL.md | READ |
| 12 | No lean mode: SKILL.md longer than 500 lines only fails a lint (the ICM skill was 594 lines) | READ |
| 13 | A non-actionable source still marks stage 02 as done, and stages 03 and 04 do not check `actionable`; approving the gate lets extraction run on it | READ |
| 14 | Re-running a stage with `--force` does not mark later stages stale | READ |
| 15 | Anthropic provider: `max_tokens=8000`, not streaming, no truncation detection, no retries for network errors, default model `claude-sonnet-4-5`; provider exceptions are not caught and surface as tracebacks | READ |
| 16 | `export` merges into an existing skill folder (`dirs_exist_ok=True`); the engine refuses to overwrite | READ |
| 17 | MCP: the per-skill tool returns the whole playbook with no matching and no "does not apply" answer; `mcp>=1.2` is unpinned (2.x removed the FastMCP import used) | READ |
| 18 | The fake provider is selectable in the production CLI and the README walkthrough, and produces plausible-looking claims ("Smaller chunks improved recall by 5 points") | READ |
| 19 | Packaging: `license = MIT` without a chosen licence; `Homepage` is the placeholder `YOUR-USER`; `.gitignore` omits `.env`; the CI publishes to PyPI on any `v*` tag (needs trusted-publishing setup; `release.sh` runs `twine upload`) | READ |
| 20 | The description pronoun check is case-sensitive and rejects quoted phrasings such as "do I need ..." (the engine hit this live) | READ |

Missing from the zip entirely: source attribution, fit check, answer rules, dual-page citations, coverage ledger, unit accounting, plan-based consolidation, `audit`, `eval-run`, `eval-quality`, provenance record, `.env` loading, run staleness.

## 4. Claims made by another assistant about the engine (checked)

- `references/provenance.json` with a source SHA-256: present in code (READ).
- `_StepDedup` in `compile.py`: present (READ).
- MCP "capability witness" matching: present as lexical unit matching, described in the tool docstring (READ). It is keyword overlap, not semantic.
- Not independently RAN beyond the engine's own tests (128 pass after commit e53aa4a).

## 5. What the project as a whole is still missing

Highest priority
1. Licence. No LICENSE file. The unpushed commit e53aa4a also added `license = { text = "MIT" }` to `engine/pyproject.toml`, contradicting the README ("no licence chosen"). Decide, then make the two agree before pushing. PyMuPDF is AGPL or commercial.
2. Answer quality is unproven. Blind judge: skill preferred in 3 of 12 pairs after three rebuilds. `eval-quality` does not yet use `expect_apply` ("should not apply") tasks or `process_checks`; samples are small; one judge model.
3. One source type only. No empirical paper, no book chapter, no source that exercises `decision_guide`, `evidence_reference`, abstention, router skills or batched consolidation on a live model.
4. No fresh QA on: plan-based consolidation, unit accounting, lean compile mode, the eval harness, artifact types and the triad test, the audit command, the modular CLI refactor.

Engine gaps found in code
5. `ingest_pdf` opens the PDF with `pymupdf.open(path)` and never closes it (use a `with` block; handles can lock files on Windows).
6. The OpenAI-compatible provider has no truncation check (`finish_reason == "length"`), no `max_tokens`, no temperature; the Anthropic provider sets no temperature or timeout.
7. CI runs only `pytest` on Ubuntu. ruff and mypy are configured in `pyproject.toml` but not run; no Windows job; no wheel build and `--help` smoke test; never observed running on GitHub.
8. Tables lose their columns in extracted text; two-column layouts may interleave; scanned PDFs abstain (no OCR).
9. Real Claude skill loading and a real MCP client have not been exercised against the generated skills.
10. `build/` holds specs and QA reports; the standard name for that is `docs/`.

Operations
11. The C: drive was 100% full (7.4 MB free of 232 GB) during this audit; some of that was temporary environments from earlier testing, since removed (about 780 MB free afterwards). Free real space before running anything heavy.
12. Two writers edited the same working tree during this session. Use one branch per writer and commit only your own work.
13. The arXiv ids cited in code comments and in the pasted literature list were not verified (the paper search tool was disconnected); treat them as unverified until checked.

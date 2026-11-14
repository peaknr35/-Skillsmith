# SPEC-V2: Skillsmith Python package
Status: DRAFT, awaiting human approval. Nothing is built until approved.
Baseline: current ICM workspace (CLAUDE.md, CONTEXT.md, _config/, stages/01-06). Kept as-is; becomes the bundled `templates/`.

## 1. What gets built (one sentence)
A pip-installable Python package `skillsmith` that ingests a PDF with PyMuPDF, segments it into sections with printed-page cites, runs the six ICM stages through a pluggable LLM (LangChain optional), validates every output against Pydantic schemas, deterministically verifies every number against a page cite, and emits a skill folder plus a Claude tool schema, system prompt and execution playbook; it also serves the finished skills over an MCP server.

## 2. Primary journey
`skillsmith init run1 --source paper.pdf` -> `skillsmith run run1` (stage 01, 02; stops at gate) -> `skillsmith approve run1 02_map` -> `run` (03, 04; stops) -> `approve run1 04_consolidate` -> `run` (05, 06) -> `skillsmith verify run1` -> `skillsmith export run1 --dest X` -> `skillsmith mcp-serve X`.

## 3. Non-goals (v1)
OCR for scanned PDFs (detect and abstain), publishing to any registry, auto-approval of gates, web UI, multi-source merging across runs, fine-tuning.

## 4. Acceptance criteria
| ID | Criterion | Verified by |
|---|---|---|
| AC1 | `ingest` on a fixture PDF writes pages.jsonl with printed_page and pdf_page, offset detected or flagged `unknown` | pytest + fixture |
| AC2 | Scanned/empty-text PDF makes ingest abstain with a specific message, no output files | pytest |
| AC3 | Segmenter splits by outline/headings; sections >8k tokens split at subheadings; every section carries page range | pytest |
| AC4 | ActionUnit/SkillSpec/SourceMap models reject a number-bearing default without `cite` | pytest vs invalid fixtures |
| AC5 | Runner builds a prompt from stage CONTEXT.md + only listed inputs; never loads full source after stage 01 | pytest (prompt inspection) |
| AC6 | LLM output that fails schema is retried up to 2 times, then stage fails with message; no partial output promoted | pytest with fake provider |
| AC7 | Gate stages (02, 04) refuse the next stage until `output/APPROVED` exists | pytest |
| AC8 | `verify` flags every number in a SKILL.md with no matching unit+cite; exit code 1 | pytest vs golden fixtures |
| AC9 | Compiler emits `skills/<name>/{SKILL.md, tool.json, system_prompt.md, playbook.md, references/evidence.md}`; tool.json is a valid Claude tool schema (name, description, input_schema JSON Schema) | pytest + schema check |
| AC10 | SKILL.md <= 500 lines, name kebab <=64, description third person | pytest |
| AC11 | MCP server (official `mcp` SDK) lists each skill as a tool and `skillsmith://<name>` resource; calling returns the playbook | pytest + in-process client |
| AC12 | `router` prints name+description prompt for non-native LLMs | pytest |
| AC13 | Package installs in a clean venv, `skillsmith --help` works, `pytest` finds >0 tests | QA install drill |
| AC14 | Provider layer: Anthropic and OpenAI-compatible via direct SDK or LangChain adapter; LangChain import is lazy and optional | pytest (import without langchain) |
| AC15 | End-to-end with FAKE provider on fixture PDF reaches exported skill with verify exit 0 | pytest e2e |
| AC16 | Live LLM run | **NOT RUN unless user supplies a key**; labeled LOCAL TESTED (fakes) |

## 5. Ownership (sequential roles, one owner per path)
- **A Content** (`src/skillsmith/templates/**`, `prompts/**`): copy of existing `_config/` + stage CONTEXT.md, plus new prompt templates for methodology extraction, trigger tests, playbook writing. Existing root files stay untouched.
- **B Engine** (`src/skillsmith/{schema,workspace,gates,verify,compile,evals}.py`, `ingest/**`): deterministic core.
- **C Interface** (`src/skillsmith/{mcp_server,cli}.py`, `pyproject.toml`, README section).
- **D Adapters** (`src/skillsmith/llm/**`, `runner.py`): providers, LangChain adapter, retry loop.
- **QA**: fresh worker, owns `tests/qa/**` only.
Shared read-only after approval: `schema.py`, `tests/fixtures/**`.

## 6. Data contracts
Schemas as in the user's sketch (Grade, SourceType, Citation, Default, Evidence, ActionUnit, SkillSpec, SourceMap) with these additions: `Citation.printed_page` required int; any `Default.value` or `Evidence.claim` containing a digit requires `cite`; `SkillSpec.role` in {router, standard}; `CompiledSkill` = {spec, tool_schema, system_prompt, playbook_md}.
Files: units as `.json` plus rendered `.md`; humans review `.md`, code validates `.json`.
Golden fixtures (`tests/fixtures/`): `sample.pdf` (generated synthetic 6-page, roman-numeral front matter, offset 3), `scanned.pdf` (image-only), `unit_valid.json`, `unit_invalid_no_cite.json`, `skill_valid.md`, `skill_unsourced_number.md`, `skillspec_valid.json`.

## 7. Interfaces
- CLI (argparse, entry `skillsmith`): init, run [--stage] [--provider anthropic|openai|fake] [--model], approve, status, verify, compile, export, router, mcp-serve.
- Provider protocol: `complete(system:str, user:str) -> str`.
- MCP: stdio transport; tools `list_skills`, `get_playbook(name)`, `get_system_prompt(name)`, plus one tool per skill from tool.json.

## 8. Human-only operations
Gate approval (`approve` writes APPROVED; never invoked by the runner), export to `~/.claude/skills`, API key entry, any live paid LLM run.

## 9. Failure handling
Missing input -> stage abstains with reason. Schema failure -> 2 retries -> fail, staging dir kept. Output written to `output.staging/`, moved to `output/` only after validation.

## 10. Delivery
`pyproject.toml` (hatchling), src layout, README, `tests/`, wheel buildable. Extras: `[langchain]`, `[anthropic]`, `[openai]`.

## 11. Interpretation register
1. argparse instead of Typer (fewer deps; Typer is not installed here). 
2. LangChain is an optional adapter, not the core; core uses the Provider protocol. `langchain_core` is not installed here, so the adapter is IMPLEMENTED/LOCAL TESTED only if it can be installed.
3. Your page citations for Ready, Fire, Aim stay UNVERIFIED; no book PDF is supplied, so no claim about it.
4. The existing `.md` workspace stays the contract source; templates are copies, not rewrites.
5. "Semantic chunking" = heading/outline-based section segmentation with token-size splitting; no embedding model.

## 12. Evidence plan
Expected levels: ingest/segment/verify/compile/gates LOCAL TESTED; e2e INTEGRATION TESTED with fake LLM; MCP INTEGRATION TESTED in-process; live LLM and real papers NOT RUN.

## 13. Approval
Approve to proceed: ________ (reply "approved" or list changes)

## 14. Amendment A1 (user message mid-build: ICM is the core)
No scope change; the contract already follows the ICM design. Made explicit and kept:
- Stage outputs keep the existing contract names: 01 `text/<id>.md`, `page-map.md`, `toc.md`; 02 `map.md` + `source_map.json`; 03 `units/<id>.md` + `.json`; 04 `consolidated/<skill>.md` + `.json`, `conflicts.md`, `ethics-log.md`; 05 `<skill>/...`, `verify-report.md`; 06 `evals/`, `eval-report.md`.
- 02 reads book self-summary/review chapters first (`ChapterTriage.self_summary`). 03 runs once per section, loading only that section. Stage prompts live in the workspace `_config/prompts/` (edit source, not output). Stage 06 failures name which `_config/` file to edit.
- Interpretation 6: stage 05 is deterministic (compiled from validated SkillSpec) so every number traces to a unit; the LLM is used in 02, 03, 04, 06 only.
- Interpretation 7: `SkillProposal` (no units) is used in the map; `SkillSpec` (with units) after consolidation.

## 15. Amendment A2 (from the pasted external review; applied after QA returns)
Decisions frozen: Click CLI, Rich output (optional, plain-text fallback), trigger-first descriptions, staged approval workflow.
1. CLI: replace argparse with Click; Rich tables/status when installed. Exit codes unchanged (1 error, 2 abstain). Interpretation 1 is withdrawn.
2. Description rule: must start with "Use when" AND be third person (no I/we/you). Enforced in SkillSpec and SkillProposal.
3. Wording: "semantic chunking" is withdrawn; it is structure-aware segmentation (outline/headings + size cap). `verify` is a mechanical citation check; it cannot prove a claim is faithful, human review of evidence quality remains.
4. Stage 04 becomes hierarchical: one call per proposed skill over only its sections' units; if a skill's units exceed a token budget, consolidate in batches then merge. Never one call over a whole book.
5. MCP skill tool: deterministic unit matching against `situation` (trigger/title overlap). Returns matched units, their boundaries to check, and an explicit "no matching unit: do not apply this skill" when nothing overlaps. It serves and selects playbook content; it does not execute the playbook or call an LLM. Tested explicitly.
6. Citations: both printed and PDF page kept (`pdf_page` filled on every citation); printed pages marked unknown when the offset is uncertain (existing page_basis=pdf fallback).
7. Evidence labeling: fake-LLM suites are LOCAL/INTEGRATION TESTED with fakes; live-model, real-PDF and real-MCP-client-session paths stay NOT RUN until performed.

## 16. Amendment A3 (after independent QA round 1 and repairs)
- A2 items implemented. Withdrawn from §7: `--provider fake` and a `compile` subcommand (fakes are injected through the Python API; compile is `run --stage 05_write`). `run` is one stage per call.
- Repairs: split_long marker/range (B2), front matter before first outline entry kept (B3), outline sorted/deduped (B4), oversize single blocks split (B5), downstream invalidation on promote (B6), unknown section ids in an edited map are a clean error (B7), mcp pinned <2, atomic promote with rollback, export checks all targets before copying, verify tokenizer fixes V1-V4, V6 (V5 documented as a limit: verify is mechanical).
- Known limits left open: "Page N" footers not detected; markers say "printed p." even under page_basis=pdf; false positives for times and versions in verify.

## 17. Amendment A4 (user decision: adopt the dual-page citation model)
`Citation.pdf_page` is required (int >= 1); `Citation.printed_page` is `int | None`, None when the printed-page offset is not established (no more printed=pdf fallback). Page markers: `[[printed p. N | pdf p. M]]` or `[[pdf p. M]]`. Stage 03 checks `pdf_page` lies in the section, rejects a `printed_page` that contradicts the page map, and fills `printed_page` from the map. Stage 04 provenance uses pdf pages. Output renders `p. N` when printed is known, else `pdf p. N`.

## 18. Amendment A5 (QA round 2 repairs)
Stage 03/04 reject proposals naming unknown section ids; `verify` refuses stale or missing stage 05; `router` on a bad path is a clean error; splitter reserves marker headroom under the cap; tokenizer handles leading-dot decimals and ignores reference numbers (Fig./Table/Section/step/page); description pronoun check covers ours/yourself/I'm and accepts "I/O"; provider exceptions become a clean StageError; MCP matcher stems and keeps only hits scoring at least half of the best, and carries tool.json parameter descriptions into the served schema.
Known limits kept: verify skips front matter, code fences and HTML comments and does not catch number words; "10:30" and version strings can be noisy; matcher is lexical, not semantic; Rich TTY rendering untested; "printed p." wording only appears in markers when a printed page is known.

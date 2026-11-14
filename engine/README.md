# Skillsmith
> From "we found" to "do this."

Skillsmith is an auditable compiler that converts procedural research papers (text PDFs) into reviewable, source-linked agent playbooks: a `SKILL.md` entry point, an execution `playbook.md`, a Claude tool schema (`tool.json`), a system prompt, and page-cited evidence (`references/evidence.md` and `references/provenance.json`). It is an ICM workspace (numbered stages, a contract per stage, human review gates) driven by a modular Python CLI package.

A summary is a failure. When a source contains an actionable procedure, descriptive claims ("we found X improves Y under Z") become procedures ("when S, do steps 1-4, use these defaults, watch for these failure modes"). When a source does not support an execution procedure, stage 02 branches to a `decision_guide`, an `evidence_reference`, or abstains cleanly.

## What is in this folder
The Python package (`src/skillsmith` with modular subcommands in `src/skillsmith/commands/`), its 128-test suite (`tests/`), the design spec and QA reports (`build/`), and notes on lessons learned (`library/`). The project overview, install and usage are in the [repository README](../README.md).

`src/skillsmith/templates/` is the bundled workspace (rules, prompts and stage contracts) that `skillsmith init` copies for each run. A bare run name such as `skillsmith run my-run` resolves inside the nearest `runs/` folder (or `$SKILLSMITH_RUNS_DIR`); a full path always works.

## Install
```bash
pip install -e .              # core: PyMuPDF, Pydantic, MCP SDK, Click, Rich
pip install -e ".[anthropic]" # or [openai] (also Ollama via OPENAI_BASE_URL), [langchain], or [dev]
```

## Run
```bash
skillsmith config                        # inspect active settings and TOML config fallbacks
skillsmith init run1 --source paper.pdf
skillsmith run run1                      # ONE stage per call: 01 ingest
skillsmith run run1                      # 02 map (triad applicability check; stops at gate)
skillsmith approve run1 02_map           # human review of stages/02_map/output/source_map.json
skillsmith run run1                      # 03 extract (one call per section)
skillsmith run run1                      # 04 consolidate (one call per skill; stops at gate)
skillsmith approve run1 04_consolidate
skillsmith run run1                      # 05 write (deterministic compile + verify)
skillsmith run run1                      # 06 eval (writes trigger and neutral-task tests)
skillsmith verify run1                   # mechanical check: every number appears in a page-cited unit
skillsmith audit run1                    # coverage ledger, 03->04 unit accounting, citation support screen
skillsmith eval-run run1                 # run trigger test + with/without-skill task comparison
skillsmith eval-quality run1             # blind A/B quality judge across repeated runs
skillsmith export run1 --dest ~/.claude/skills
skillsmith mcp-serve ~/.claude/skills    # serve skills to Claude over MCP (stdio)
skillsmith router ~/.claude/skills       # name+description router prompt for LLMs without skills
```
Click drives the CLI (`src/skillsmith/commands/`); Rich adds tables, status spinners, and colour on a terminal (plain text when piped).
Providers: `--provider anthropic` (needs `ANTHROPIC_API_KEY`), `openai` (any OpenAI-compatible server), `langchain --model "provider:model"`.

## Pipeline
```
01 ingest (PyMuPDF, deterministic) -> 02 map [GATE] -> 03 extract (per section) -> 04 consolidate [GATE]
 -> 05 write (deterministic) -> 06 eval
```
- Scoped context: stage 03 loads one section plus the extraction guide, never the whole source.
- Rules live in `_config/` and `_config/prompts/`. When a skill comes out wrong, edit those, not the output.
- Schemas (`schema.py`) reject any default or evidence item without a page cite. Descriptions must start with `Use when` and be third person.
- Segmentation is structure-aware (PDF outline or heading patterns, then a token cap), not embedding-based semantic chunking.
- Consolidation (04) is hierarchical: one call per proposed skill; a skill over the token budget is consolidated in batches and then merged. Every extracted unit is accounted for in `accounting.md` (zero silent drops).
- Deterministic checks on model output: cited pages must lie in the section, `quote_hint` must appear verbatim, every number must occur in the section text (stage 03) or in the extracted units (stage 04). Failures retry twice, then stop.
- Output is written to `output.staging/` and promoted only after validation. Re-running a gate stage revokes its `APPROVED`.
- Citations carry `pdf_page` (always) and `printed_page` (only when the offset was established; otherwise `null`, never guessed). Stage 03 rejects a cite outside the section's PDF pages or a printed page that disagrees with the page map, and fills `printed_page` from the map. Compiled skills show `p. N` (printed) or `pdf p. N` (printed unknown).

## What a generated skill looks like
```
<skill>/SKILL.md  playbook.md  tool.json  system_prompt.md  references/evidence.md  references/provenance.json
```

## MCP
`mcp-serve` exposes `list_skills`, `get_playbook`, `get_system_prompt`, one tool per skill and one `skillsmith://<name>` resource per skill. A skill tool *selects* playbook units whose trigger/title words overlap the `situation` and returns them with the boundaries to check; with no overlap it answers `NO MATCH` and says not to apply the skill. It does not execute the playbook or call an LLM. Requires the `mcp` 1.x SDK (pinned `<2`).

## Honest status & limits (v0.2)
- **Unit & regression suite:** 128 tests (`pytest`), exercising the pipeline checks, config resolution, CLI subcommands, and MCP server with a scripted fake LLM and synthetic PDFs.
- **Live paper validation:** Tested end-to-end on the 21-page *Interpretable Context Methodology* paper (arXiv:2603.16021) using live Claude models, passing `verify` and `audit` (0 unaccounted sections, 32 extracted units consolidated into 21 with 0 silent drops), and evaluated with `eval-run` and `eval-quality` (blind A/B judging). See the [root README](../README.md#how-well-does-it-work) for full evaluation details.
- Re-running a stage invalidates every later stage (they show as pending).
- Printed-page offset detection needs bare page-number blocks; 'Page N' footers leave printed pages unknown (`page_basis=pdf`, citations use PDF pages only).
- No OCR: scanned PDFs make stage 01 abstain.
- `verify` is a mechanical citation check, and `audit` checks lexical support on cited pages. Neither proves a claim is semantically faithful to the source; a human reviews evidence quality at the gates.
- Tests: `pip install -e ".[dev]" && pytest`.

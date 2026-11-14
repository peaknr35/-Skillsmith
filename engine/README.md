# Skillsmith
> From "we found" to "do this."

Skillsmith turns a research paper, article or book (PDF) into agent skills: a `SKILL.md`, a Claude tool schema (`tool.json`), a system prompt, an execution playbook and page-cited evidence. It is an ICM workspace (numbered stages, a contract per stage, human review gates) driven by a Python package.

A summary is a failure. Descriptive claims ("we found X improves Y under Z") become procedures ("when S, do steps 1-4, use these defaults, watch for these failure modes").

## What is in this folder
The Python package (`src/skillsmith`), its tests (`tests/`), the design spec and QA reports (`build/`) and notes on lessons learned (`library/`). The project overview, install and usage are in the [repository README](../README.md).

`src/skillsmith/templates/` is the bundled workspace (rules, prompts and stage contracts) that `skillsmith init` copies for each run. A bare run name such as `skillsmith run my-run` resolves inside the nearest `runs/` folder (or `$SKILLSMITH_RUNS_DIR`); a full path always works.

## Install
```bash
pip install .                 # core: PyMuPDF, Pydantic, MCP SDK
pip install ".[anthropic]"    # or [openai] (also Ollama via OPENAI_BASE_URL) or [langchain]
```

## Run
```bash
skillsmith init run1 --source paper.pdf
skillsmith run run1                      # ONE stage per call: 01 ingest
skillsmith run run1                      # 02 map (stops at the gate)
skillsmith approve run1 02_map           # human review of stages/02_map/output/source_map.json
skillsmith run run1                      # 03 extract (one call per section)
skillsmith run run1                      # 04 consolidate (one call per skill; stops at the gate)
skillsmith approve run1 04_consolidate
skillsmith run run1                      # 05 write (deterministic compile + verify)
skillsmith run run1                      # 06 eval (writes tests; does not run them)
skillsmith verify run1                   # mechanical check: every number appears in a page-cited unit
skillsmith export run1 --dest ~/.claude/skills
skillsmith mcp-serve ~/.claude/skills    # serve skills to Claude over MCP (stdio)
skillsmith router ~/.claude/skills       # name+description router prompt for LLMs without skills
```
Click drives the CLI; Rich adds tables and colour on a terminal (plain text when piped).
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
- Consolidation (04) is hierarchical: one call per proposed skill; a skill over the token budget is consolidated in batches and then merged. No call sees a whole book.
- Deterministic checks on model output: cited pages must lie in the section, `quote_hint` must appear verbatim, every number must occur in the section text (stage 03) or in the extracted units (stage 04). Failures retry twice, then stop.
- Output is written to `output.staging/` and promoted only after validation. Re-running a gate stage revokes its `APPROVED`.
- Citations carry `pdf_page` (always) and `printed_page` (only when the offset was established; otherwise `null`, never guessed). Stage 03 rejects a cite outside the section's PDF pages or a printed page that disagrees with the page map, and fills `printed_page` from the map. Compiled skills show `p. N` (printed) or `pdf p. N` (printed unknown).

## What a generated skill looks like
```
<skill>/SKILL.md  tool.json  system_prompt.md  playbook.md  references/evidence.md
```

## MCP
`mcp-serve` exposes `list_skills`, `get_playbook`, `get_system_prompt`, one tool per skill and one `skillsmith://<name>` resource per skill. A skill tool *selects* playbook units whose trigger/title words overlap the `situation` and returns them with the boundaries to check; with no overlap it answers `NO MATCH` and says not to apply the skill. It does not execute the playbook or call an LLM. Requires the `mcp` 1.x SDK (pinned `<2`).

## Honest limits (v0.2)
- Re-running a stage invalidates every later stage (they show as pending).
- Printed-page offset detection needs bare page-number blocks; 'Page N' footers leave printed pages unknown (`page_basis=pdf`, citations use PDF pages only).
- No OCR: scanned PDFs make stage 01 abstain.
- Tested with a scripted fake LLM and a synthetic PDF. Not yet run against a live model or a real paper/book.
- `verify` is a mechanical citation check. It cannot prove a claim is faithful to the source; a human reviews evidence quality at the gates. A number that appears anywhere in a unit's own text passes.
- Stage 06 writes trigger and task tests; it does not run the with/without-skill comparison.
- Example page cites for *Ready, Fire, Aim* in the design notes are unverified until a source PDF is run through stage 05 verify.
- Tests: `pip install ".[dev]" && pytest`.

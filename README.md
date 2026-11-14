# Skillsmith

> From "we found" to "do this."

Skillsmith is an auditable compiler that converts procedural research papers into reviewable, source-linked agent playbooks (`SKILL.md`, `playbook.md`, `tool.json`, `system_prompt.md`, and `references/evidence.md`), and tests whether those playbooks actually help on real tasks.

Not every paper should become an execution skill. Skillsmith runs a six-stage pipeline with an applicability gate (choosing between an execution skill, a decision guide, an evidence reference, or explicit abstention), two human review gates, deterministic provenance checks (dual-page citations, verbatim quote checks, zero silent unit drops, and mechanical number verification), and blind A/B evaluation against the base model.

Skillsmith records whether identified sections and extracted units are accounted for, checks citations mechanically, and evaluates generated playbooks on specified tasks. These checks can reveal omissions and unsupported claims, but human review is still needed to judge whether the extraction faithfully represents the source (a step can quote a real phrase and still invert its meaning). The two review gates require a human reading the source.

## What you get

For each skill:

```
<skill>/
  SKILL.md                  the lean entry point (500 lines at most): fit check, unit index, steps, defaults
  playbook.md               boundaries, pitfalls and worked examples for every unit
  references/evidence.md    evidence grades, page cites, and the source units each unit was built from
  tool.json                 a Claude tool schema (for MCP or other runtimes)
  system_prompt.md          a system-prompt fragment for LLMs without native skill support
```

A real example, built from the paper *Interpretable Context Methodology* (arXiv 2603.16021), is in [`skills/folder-structured-agent-workflows`](skills/folder-structured-agent-workflows).

## How it works

```
01 ingest -> 02 map [gate] -> 03 extract -> 04 consolidate [gate] -> 05 write -> 06 eval
```

| Stage | What happens | Uses an LLM |
|---|---|---|
| 01 ingest | PyMuPDF text, printed-vs-PDF page offset, outline-based sections | no |
| 02 map | Is the source actionable? Triage every section, propose skills. Stops and abstains if nothing would change what a practitioner does | yes |
| 03 extract | One call per section: action units (trigger, steps, defaults, boundaries, failure modes, graded evidence). Rejects invented numbers, quotes not on the cited page, cites outside the section | yes |
| 04 consolidate | The model returns a small merge plan; code builds the merged units from the originals, so cites and numbers are inherited. Every extracted unit must be carried or excluded with a reason | yes |
| 05 write | Compiles the files above and checks that every number appears in a page-cited unit | no |
| 06 eval | Writes trigger tests and neutral-task tests | yes |

Each stage loads only its own contract and inputs, never the whole book. Bad output is fixed by editing the rules and prompts in the workspace's `_config/`, not by hand-editing the generated skill.

## Install

Python 3.10 or newer. Not on PyPI; install from source.

```bash
git clone https://github.com/peaknr35/-Skillsmith.git
cd -- -Skillsmith/engine
pip install -e ".[anthropic]"     # or ".[openai]" (also Ollama via OPENAI_BASE_URL) or ".[langchain]"
```

Put your key in a `.env` file (never committed) in the current folder, the run folder, or any of their four parent folders, or set it in the environment. Variables already set in the environment win over `.env`:

```
ANTHROPIC_API_KEY=...
```

## Use it

```bash
skillsmith init my-run --source paper.pdf
skillsmith run my-run --provider anthropic    # one stage per call; 01 ingest
skillsmith run my-run --provider anthropic    # 02 map, stops at the review gate
skillsmith approve my-run 02_map              # after you read stages/02_map/output/source_map.json
skillsmith run my-run --provider anthropic    # 03 extract
skillsmith run my-run --provider anthropic    # 04 consolidate, stops at the gate
skillsmith approve my-run 04_consolidate      # after you read conflicts.md and accounting.md
skillsmith run my-run --provider anthropic    # 05 write
skillsmith run my-run --provider anthropic    # 06 eval
skillsmith export my-run --dest ~/.claude/skills
```

`skillsmith compile my-run` runs every remaining stage through 05 in one go and stops with an error at an unapproved gate. `skillsmith status my-run` shows where a run is. `--stage 03_extract` re-runs one stage (this also marks every later stage pending).

### Check what it made

| Command | What it does |
|---|---|
| `skillsmith config` | Show active configuration settings, resolved layer precedence, and warnings |
| `skillsmith verify my-run` | Mechanical check: every number in the output appears in a page-cited unit |
| `skillsmith audit my-run` | Section coverage ledger, unit accounting from stage 03 to 04, and a step-to-page citation screen |
| `skillsmith eval-run my-run` | Trigger test (skill among distractors) and a with/without-skill task comparison |
| `skillsmith eval-quality my-run` | Blind answer-quality judge: repeated answers with and without the skill, scored in random order on generic criteria that never mention the skill |

### Use the skills

- **Claude Code:** `skillsmith export` copies the skill folders into `~/.claude/skills`.
- **MCP:** `skillsmith mcp-serve <skills-dir>` serves each skill as a tool; it selects playbook units by keyword overlap and says "no match" rather than guessing.
- **Other LLMs:** `skillsmith router <skills-dir>` prints a name-and-description prompt to use as a router.

## How well does it work?

Honest status, v0.2:

- **Tests:** a test suite (`engine/tests`), all with a scripted fake LLM and synthetic PDFs. They test the pipeline's checks, not the quality of any generated skill. No fresh-eyes review has covered the newest changes.
- **Real run:** one paper (the 21-page ICM paper) went through every stage on a live model, with two human gates. The audit shows no unaccounted sections and no dropped units (32 extracted, 21 consolidated), and all 21 units have lexical citation support on their cited pages. That check is a screen, not proof a claim is faithful.
- **Does the skill improve answers?** Not shown. In a blind judge test (12 comparisons per run, Sonnet 5.5 answering, Opus 5.5 judging), answers without the skill were preferred in 10, 9 and 9 of 12 across three successive rebuilds of the skill. Rebuilds fixed real problems the judge named (unexplained sources, internal ids and page cites leaking into answers), and the gap narrowed, but the skill still lost more often than it won, and it won most clearly when the user asked about the paper itself. The source paper itself reports no controlled comparison against ordinary good practice. Treat the generated skill as a way to apply that method, not as proof it beats generic advice.

## Limits

- No OCR: scanned PDFs make stage 01 stop with a clear message.
- Tables lose their column alignment in extracted text.
- Printed-page detection needs bare page-number lines; "Page N" footers leave printed pages unknown and citations fall back to PDF pages.
- `verify` is a mechanical check. It skips worked examples, cannot read number words, and cannot judge whether a claim is faithful. Review evidence grades and conflicts at the gates.
- Only one source has run live. Books, empirical papers and other source types are untested.

## Repository layout

| Path | What it is |
|---|---|
| `engine/` | The Python package (`src/skillsmith`), tests, the spec and QA reports (`build/`) and lessons (`library/`) |
| `skills/` | Skills: one built by Skillsmith from a paper, and `skillsmith-pipeline`, which teaches an agent to run Skillsmith |
| `.github/` | CI: lint, type check and tests on Linux and Windows, plus a wheel build-and-run check |

Runs (`runs/`) and source PDFs are not committed.

## Model settings (optional)

Nothing below is sent unless you set it, so no model or server receives a parameter it might reject:

| Variable | Effect |
|---|---|
| `SKILLSMITH_PROVIDER` | `anthropic`, `openai` or `langchain` (default `anthropic`) |
| `SKILLSMITH_MODEL` | Model name (the Anthropic default is `claude-sonnet-5-5`) |
| `SKILLSMITH_BASE_URL` | Server URL for the `openai` provider (e.g. Ollama); `OPENAI_BASE_URL` also works |
| `SKILLSMITH_RUNS_DIR` | Folder where bare run names live (a typo here is created by `init`, so check the spelling) |
| `SKILLSMITH_MAX_TOKENS` | Reply limit (Anthropic default 32000; unset for OpenAI-compatible servers) |
| `SKILLSMITH_TEMPERATURE` | Sampling temperature, e.g. `0` for more repeatable extraction |
| `SKILLSMITH_TIMEOUT` | Request timeout in seconds |

A reply cut off by the limit is an explicit error for both provider families, never a silently truncated result. A bad value (`inf`, `0`, a negative or non-numeric number) is an error that names the variable.

### Config files

`provider`, `model`, `base_url` and `runs_dir` can also be set in a TOML file. Highest priority first: command-line flags, `SKILLSMITH_*` variables, a file given with `skillsmith --config FILE`, `./skillsmith.toml`, `~/.config/skillsmith/config.toml`. Each key is checked on its own; a bad key is ignored with a warning that names the key (never its value). `skillsmith config` shows the result.

## Development

```bash
cd engine
pip install -e ".[dev]"
ruff check . && mypy src && pytest
```

## Licence

No licence has been chosen yet, so by default all rights are reserved. The PDF library used, PyMuPDF, is AGPL or commercially licensed, which matters for any reuse; choose a licence deliberately before relying on this elsewhere.

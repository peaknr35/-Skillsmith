# Skillsmith
> From "we found" to "do this."

Badges (PyPI, license, CI)

## What it does
2-3 sentences + before/after (paper excerpt -> generated SKILL.md excerpt)

## Why not just summarize?
Descriptive vs procedural; summary-as-skill fails.

## Quick start
pip install skillsmith
skillsmith init my-run --source paper.pdf
skillsmith run my-run

## How it works
Pipeline diagram (mermaid): ingest -> map -> [gate] -> extract -> consolidate -> [gate] -> write -> eval
Principles: scoped context per stage, human gates, edit-source-not-output

## CLI reference
## Output: what a generated skill looks like (folder tree)
## Configuration (_config/, models, providers)
## Using skills with Claude / other LLMs (router prompt)
## Safety and quality rules (no invented numbers, page cites, evidence grades, ethics filter)
## Examples (ICM paper, Ready, Fire, Aim)
## Roadmap
## Contributing / License
## Credits (ICM paper, Anthropic skill-creator)

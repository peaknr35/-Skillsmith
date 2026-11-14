# Stage 03_extract
## Inputs
ONE chapter file + _config/extraction-guide.md + map.md row
## Process
Extract action units per extraction-guide. Anecdote chapters: only worked examples. Split chapters >8k tokens by subheading.
## Outputs
units/ch##.md
## Gate
Run once per chapter; never load other chapters.
## Verify
Check outputs against _config/quality-checklist.md before finishing.

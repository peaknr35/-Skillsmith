# Skillsmith: where everything is

```
E:\Skillsmith\
  engine\        the Python tool (src\skillsmith, tests, pyproject.toml), its spec and QA reports (build\), lessons (library\)
  runs\          one workspace per source document, created by `skillsmith init`
    icm-paper\       the good run on the ICM paper (all six stages done); stages\05_write\output\ holds its skill
    icm-paper-old\   an earlier, superseded run (kept, not deleted)
    _sources\        the original PDFs
  skills\        finished skills, one folder each
    folder-structured-agent-workflows\   built from the ICM paper
    skillsmith-pipeline\                 how an agent runs this pipeline
  .env           your API key (ANTHROPIC_API_KEY=...); never committed; found automatically from engine\ or runs\
  source-to-skill\   the ORIGINAL workspace template folder, left in place (see below)
```

Installed for Claude Code (separate copies, in your user skills folder): `%USERPROFILE%\.claude\skills\folder-structured-agent-workflows` and `%USERPROFILE%\.claude\skills\skillsmith-pipeline`.

## Everyday commands (run from E:\Skillsmith\engine)
```
skillsmith init my-run --source path\to\paper.pdf      # creates E:\Skillsmith\runs\my-run
skillsmith run my-run --provider anthropic              # one stage per call; stops at review gates
skillsmith approve my-run 02_map                        # you approve gates
skillsmith export my-run --dest E:\Skillsmith\skills      # copy finished skills out
```
A bare run name resolves inside the nearest `runs` folder (or `$SKILLSMITH_RUNS_DIR`); a full path always works too.

## What is left in source-to-skill
`CLAUDE.md`, `CONTEXT.md`, `_config\`, `stages\` (empty contracts): the original ICM template, now a second copy of what the engine bundles in `engine\src\skillsmith\templates`.
Also `stages\01_ingest\real-docs\run-icm2`: the ORIGINAL copy of the run that now lives in `runs\icm-paper`. It could not be moved because Windows reported a file inside it as open. Close whatever holds it (an editor tab, file preview or terminal), then delete it. Nothing in it is needed.

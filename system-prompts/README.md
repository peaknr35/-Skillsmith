# system-prompts

Only system prompts live here. Nothing else: no skills, no run output, no code.

Put a prompt you consider high quality in its own file, so it can be read, compared and reused.

## One prompt, one file

Name files `<topic>-<what-it-does>.md`, for example `code-review-strict-reviewer.md`.

Start each file with a short header, then the prompt itself, unchanged:

```
---
name: code-review-strict-reviewer
source: where it came from (URL, book, product, or "written by me")
date_added: 2026-11-15
status: raw | cleaned | tested
notes: anything you know about when it works or fails
---

<the system prompt text, exactly as extracted>
```

`status` is honest bookkeeping:
- `raw`: pasted as found, not yet read closely
- `cleaned`: you removed vendor-specific bits, kept the meaning
- `tested`: run against a model on real tasks (say how in `notes`)

## Rules

- Keep the original wording. If you edit it, save the edit as a new file and keep the original.
- Record the source. A prompt with no source is hard to trust or credit.
- Do not put secrets, API keys or private customer text in a prompt file. This folder is committed to git.
- Check the source's terms before committing a prompt you did not write. Some are copyrighted; if unsure, keep the file out of git (add it to `.gitignore`) or store a link and your own notes instead.

## How it connects to Skillsmith

Skillsmith does not read this folder yet. Today a skill's `system_prompt.md` is generated per run. These files are a reference library you can compare against that output, or later feed to `eval-quality` as the baseline arm.

## Reference libraries

- `dsh-superagent/`: pinned copy of DeepSeek's research prototype prompts, skills and docs (MIT). See its README for provenance and what has and has not been read.
- `general/`: host-neutral modules rewritten from those patterns for Skillsmith's own stages. All `raw` and untested; see its README.

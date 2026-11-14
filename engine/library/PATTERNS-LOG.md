# Patterns log (candidates, not approved)
Source build: Skillsmith v0.2 (this repo). Evidence: 63 fake-LLM tests, two independent QA rounds. Not yet reused on another project.

1. Candidate: contract-first with golden fixtures caught nothing the QA agent did not also find in regexes and segmentation; what paid off was an independent adversarial pass with its own PDFs.
2. Candidate: any "verify numbers" tool needs a tokenizer test table (ranges, glued units, comma lists, leading-dot decimals, reference numbers). Scope: text-checking tools.
3. Candidate: pin the major version of a fast-moving SDK (mcp <2) in the first commit; a clean install on a new machine pulled a breaking major.
4. Candidate: when a page marker and its content are separated by a splitter, ranges silently go wrong; assert "every part starts with a marker, none ends with one" on every splitter.
5. Candidate: re-running an upstream stage must invalidate downstream stages and their approvals (stale outputs otherwise pass checks).
6. Risk note: shell heredocs in this environment altered backslash escapes in regexes (a backspace character ended up in a pattern). Write regex-bearing files with the file tool, then grep for control characters.
Review date: after the first run on a real paper.

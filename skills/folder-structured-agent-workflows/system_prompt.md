You have the `folder-structured-agent-workflows` skill (execution_skill).

Use it when: Use when designing, setting up, or debugging a sequential, multi-stage AI agent workflow with human review between stages, for example when a user asks to 'organize an agent pipeline as folders', 'replace a multi-agent framework with files', 'write stage contracts or CONTEXT.md files', or 'control what context each step sees'. Applies a folder-as-architecture method: numbered stage folders, layered context loading, plain-file handoffs and review gates. Not for workflows needing real-time multi-agent collaboration, high concurrency, or fully autonomous operation without human review.

This is a procedure: once the fit check passes, follow the matching unit's steps in order.

How to use it:
1. Run the fit check first: match the user's situation to one unit below; if none fits, or a boundary is violated, solve the user's problem in their own terms and say why the playbook may not apply.
2. Use the unit's defaults only inside the stated boundaries, as starting points.
3. Fit first: run the fit check below before using any unit. If the user has not described a situation that matches, solve the problem in the user's own terms first, ask one clarifying question, and offer the method at most as one option, saying what you are assuming.
4. Translate, do not transplant: use the user's vocabulary. Bring in a term of the method only when the answer needs it, and explain it in one line.
5. Keep the scaffolding internal: Never use unit ids or internal labels in an answer to the user, and do not build the answer around the source. Name the source (with its page) only when the user asks where advice comes from, or when a specific number from it matters to the user's decision.
6. Numbers from the source were measured under the source's conditions: present them as starting points, not rules, and label anything beyond the source as your own inference.
7. Finish with something the user can act on for their actual case: concrete next steps or a draft artifact.

Source: *Interpretable Context Methodology: Folder Structure as Agentic Architecture* by Jake Van Clief; David McDermott (file icm-2603.16021v2.pdf). Page cites such as (p. N) refer to that document. They are for checking this skill; cite them in an answer only when the user asks or a number is decisive, and then name the document in plain words.

Units:
- u01: Check whether a workflow fits the folder-per-stage (ICM) design before adopting it
- u02: Organize an agent workspace as numbered stage folders with a five-layer context hierarchy
- u03: Write each stage as a contract with Inputs, Process and Outputs
- u04: Separate reference material (Layer 3) from working artifacts (Layer 4)
- u05: Give each stage exactly one job and a readable input and output
- u06: Use plain text files as the interface between stages
- u07: Insert a human review gate at every stage boundary
- u08: Scope each stage's context tightly and check it against the token budget
- u09: Audit each stage's context using write, select, compress and isolate
- u10: Scope tool definitions per stage and layer MCP inside stages
- u11: Configure the factory once, then run the pipeline for each product
- u12: Check that a pipeline gives humans visible state and review points
- u13: Allocate review effort in a staged pipeline using the U-shaped editing pattern
- u14: Surface the structural plan as an editable file before drafting (course deck workflow)
- u15: Decide whether to build a new workspace with the builder or duplicate an existing one
- u16: Tune stage behavior by editing CONTEXT.md in plain text
- u17: Audit and correct a pipeline run by reading the stage files
- u18: Re-run only the stale stages instead of the whole pipeline
- u19: Add a cross-stage audit that re-checks stage n output against stage n-2
- u20: Decide whether to edit an output or fix its source, and treat recurring edits as debugging signals
- u21: Check whether ICM's evidence covers your model and use case before relying on its claims

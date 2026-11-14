---
name: folder-structured-agent-workflows
description: "Use when designing, setting up, or debugging a sequential, multi-stage AI agent workflow with human review between stages, for example when a user asks to 'organize an agent pipeline as folders', 'replace a multi-agent framework with files', 'write stage contracts or CONTEXT.md files', or 'control what context each step sees'. Applies a folder-as-architecture method: numbered stage folders, layered context loading, plain-file handoffs and review gates. Not for workflows needing real-time multi-agent collaboration, high concurrency, or fully autonomous operation without human review."
---

# Folder structured agent workflows

Source: *Interpretable Context Methodology: Folder Structure as Agentic Architecture* by Jake Van Clief; David McDermott (file icm-2603.16021v2.pdf). Page cites such as (p. N) refer to that document. They are for checking this skill; cite them in an answer only when the user asks or a number is decisive, and then name the document in plain words.

## How to use
This is a procedure: once the fit check passes, follow the matching unit's steps in order.

1. Fit first: run the fit check below before using any unit. If the user has not described a situation that matches, solve the problem in the user's own terms first, ask one clarifying question, and offer the method at most as one option, saying what you are assuming.
2. Match the user's situation to one unit in the index below; if none fits, say the situation is outside this skill. Before applying a unit, read its boundaries and pitfalls in playbook.md (search for its unit id) and do not apply it if a boundary is violated.
3. Translate, do not transplant: use the user's vocabulary. Bring in a term of the method only when the answer needs it, and explain it in one line.
4. Keep the scaffolding internal: Never use unit ids or internal labels in an answer to the user, and do not build the answer around the source. Name the source (with its page) only when the user asks where advice comes from, or when a specific number from it matters to the user's decision.
5. Numbers from the source were measured under the source's conditions: present them as starting points, not rules, and label anything beyond the source as your own inference.
6. Finish with something the user can act on for their actual case: concrete next steps or a draft artifact.

## Fit check (run before applying anything below)
Apply this skill only when the user's situation matches. If it does not, or the user has not said, answer in the user's own terms and ask one clarifying question.
Decision units to run first: `u01` Check whether a workflow fits the folder-per-stage (ICM) design before adopting it; `u15` Decide whether to build a new workspace with the builder or duplicate an existing one; `u20` Decide whether to edit an output or fix its source, and treat recurring edits as debugging signals; `u21` Check whether ICM's evidence covers your model and use case before relying on its claims.
Do not apply (or adapt first) when:
- Do not apply when: real-time multi-agent collaboration with dynamic message passing in tight loops. File-based sequential handoffs are too slow.
- Do not apply when: high-concurrency, many simultaneous users. This needs queueing, state isolation and deployment infrastructure, and ICM is local-first by design.
- Do not apply when: complex automated branching based on AI decisions mid-pipeline. It would need scripting that moves ICM toward being a framework itself.
- The authors do not claim ICM replaces existing tools across the board, only that for a large, common class of workflows they add more complexity than needed.
- The conclusion's claim of full pipeline capability with no framework, no server and no developer for day-to-day operation is scoped to workflows that are sequential, reviewable, and repeatable.
- The authors call the filesystem the simplest viable architecture for this class of problem, not for every AI workflow.
- The design uses one agent reading different context at each stage, not multiple agents coordinating through code.
- Folder approach is simpler for: changing stage order (a rename or reorder of folders instead of editing orchestration code and redeploying), modifying a prompt (edit a markdown file), adding or removing a stage (add or delete a folder), inspecting intermediate state (open the folder and read the files), hand-off (copy the folder), and who can make changes (anyone with a text editor instead of a developer).
- Do NOT apply the folder approach, or expect it to match frameworks, when you need built-in retry, fallback and exception handling. Error recovery there is a manual re-run of the failed stage with a human deciding between stages.
- Do NOT apply it for conditional branching that needs programmatic routing on agent output; the folder approach is sequential by design.
- ...53 more boundaries in playbook.md.

## Unit index
- `u01` Check whether a workflow fits the folder-per-stage (ICM) design before adopting it. When: Deciding between ICM (folder-based staged pipeline) and a multi-agent framework such as AutoGen
- `u02` Organize an agent workspace as numbered stage folders with a five-layer context hierarchy. When: Designing a multi-step agent workflow and deciding how to give each step its context
- `u03` Write each stage as a contract with Inputs, Process and Outputs. When: Creating or revising a stage's CONTEXT.md
- `u04` Separate reference material (Layer 3) from working artifacts (Layer 4). When: Persistent rules (voice, design system, conventions) and per-run content are mixed in one prompt or file
- `u05` Give each stage exactly one job and a readable input and output. When: A stage's instructions cover several different operations
- `u06` Use plain text files as the interface between stages. When: Choosing a format for passing data between agent steps
- `u07` Insert a human review gate at every stage boundary. When: Building a content pipeline (research to script to production) with an AI agent
- `u08` Scope each stage's context tightly and check it against the token budget. When: Prompt contains all stage instructions, all reference files and all prior outputs
- `u09` Audit each stage's context using write, select, compress and isolate. When: User asks how to structure context for an agent
- `u10` Scope tool definitions per stage and layer MCP inside stages. When: Agent is slow or costly because many tool definitions are loaded upfront
- `u11` Configure the factory once, then run the pipeline for each product. When: Repeating the same kind of deliverable many times
- `u12` Check that a pipeline gives humans visible state and review points. When: User is designing human oversight for an AI workflow
- `u13` Allocate review effort in a staged pipeline using the U-shaped editing pattern. When: Deciding where to spend limited human review time in a multi-stage agent workflow
- `u14` Surface the structural plan as an editable file before drafting (course deck workflow). When: Producing slide decks or other long artifacts from unstructured source material
- `u15` Decide whether to build a new workspace with the builder or duplicate an existing one. When: Need a workspace for a new domain or content format
- `u16` Tune stage behavior by editing CONTEXT.md in plain text. When: Output tone or length is off in a particular stage
- `u17` Audit and correct a pipeline run by reading the stage files. When: Need to see why a pipeline produced a given output
- `u18` Re-run only the stale stages instead of the whole pipeline. When: Research output is fine but the script needs rework
- `u19` Add a cross-stage audit that re-checks stage n output against stage n-2. When: Final-stage output drifts from earlier decisions, such as timing, pacing or revised phrases
- `u20` Decide whether to edit an output or fix its source, and treat recurring edits as debugging signals. When: You keep making the same manual edit to a stage's output
- `u21` Check whether ICM's evidence covers your model and use case before relying on its claims. When: Considering ICM for a model other than Claude Opus 4.6 or Sonnet 4.6

## Procedure
### Check whether a workflow fits the folder-per-stage (ICM) design before adopting it
<!-- unit:u01 -->
When: Deciding between ICM (folder-based staged pipeline) and a multi-agent framework such as AutoGen; User describes a repeatable multi-step AI workflow and asks what architecture to use

1. Test the workflow on three properties: sequential (step 2 follows step 1), reviewable (a human should check each step's output), repeatable (the same pipeline runs repeatedly, e.g. weekly or daily, with different input).
2. If all three hold, use ICM: stage folders and file handoffs, with no framework code, server infrastructure or developer dependency for day-to-day operation.
3. Check the exclusions: do agents need to talk to each other dynamically in tight loops? Do many users hit the same pipeline at once? Must the AI itself decide branching mid-pipeline?
4. If any exclusion applies, do not use ICM for that part. Use a multi-agent or queueing framework instead.
5. If branching is needed but a human can decide, keep ICM and have the human choose the next stage between stages (for example run stage 3a instead of 3b after reading the stage 2 output).

Boundaries and pitfalls: playbook.md, unit u01.

### Organize an agent workspace as numbered stage folders with a five-layer context hierarchy
<!-- unit:u02 -->
When: Designing a multi-step agent workflow and deciding how to give each step its context; Agent prompts keep growing as stages and reference files are added

1. Create the workspace as one folder.
2. Put a global identity file (Layer 0, CLAUDE.md) at the root. It says which workspace the agent is in, what the folders contain, and where to find things.
3. Add a workspace-level routing file (Layer 1, CONTEXT.md). It maps what the user wants to do to the stage that handles it and lists shared resources.
4. Give each stage its own folder with a stage contract (Layer 2, CONTEXT.md) defining inputs, process and outputs.
5. Put stable reference material (Layer 3) in references/, _config/ and shared/ folders.
6. Put per-run working artifacts (Layer 4) in each stage's output/ folder.
7. Number stage folders (01_, 02_, ...) so the numbering encodes execution order.
8. Load for each stage only the layers it needs. A rendering-type stage may need only Layers 0-2. A writing stage reads down to Layer 4 for rules and source material.

| Parameter | Value | Tested range | Source |
|---|---|---|---|
| Layer 0 (CLAUDE.md) size | ~800 tokens | - | p. 5 |
| Layer 1 (workspace CONTEXT.md) size | ~300 tokens | - | p. 5 |
| Layer 2 (stage CONTEXT.md) size | 200-500 tokens | - | p. 5 |
| Layer 3 (reference material) size | 500-2k tokens | - | p. 5 |

Boundaries and pitfalls: playbook.md, unit u02.

### Write each stage as a contract with Inputs, Process and Outputs
<!-- unit:u03 -->
When: Creating or revising a stage's CONTEXT.md; An agent loads too much or the wrong files for a step

1. In the stage's CONTEXT.md, write an Inputs section that lists exactly which files to load, and which sections of them if only part is relevant.
2. Label each input as Layer 4 (working, from the previous stage's output/ folder) or Layer 3 (reference, such as _config/voice.md or references/structure.md).
3. Write a Process section with short instructions that point to the reference files, e.g. follow the structure in one file and match the tone in another.
4. Write an Outputs section naming each file and the output/ folder it is written to.
5. Have the agent read the CONTEXT.md, follow it, and write the output.
6. Let the next stage read whatever is in the output folder, including human edits.

Boundaries and pitfalls: playbook.md, unit u03.

### Separate reference material (Layer 3) from working artifacts (Layer 4)
<!-- unit:u04 -->
When: Persistent rules (voice, design system, conventions) and per-run content are mixed in one prompt or file; Setting up a workspace that will be run repeatedly

1. For each file ask: does it change between runs? If no, it is Layer 3 reference. If yes, it is Layer 4 working artifact.
2. Put Layer 3 files (e.g. voice.md, design-system.md, conventions.md) in references/, _config/ or shared/, and configure them once during workspace setup.
3. Put Layer 4 files (e.g. research-output.md, script-draft.md) in the stage output/ folders. They are produced during each pipeline run.
4. In stage instructions, tell the model to internalize Layer 3 as constraints and to process Layer 4 as input to transform.
5. Never store per-run content in the reference folders or persistent rules in output/.

Boundaries and pitfalls: playbook.md, unit u04.

### Give each stage exactly one job and a readable input and output
<!-- unit:u05 -->
When: A stage's instructions cover several different operations; Debugging which step produced a bad result

1. List the workflow's steps and assign each to one stage folder.
2. Check that each stage does only one thing; for example a stage that fetches data does not also filter it, and a stage that filters does not also format the final output.
3. Define for each stage a specific input it reads and a specific output it writes to its own folder.
4. If a stage does two jobs, split it into two stages.

Boundaries and pitfalls: playbook.md, unit u05.

### Use plain text files as the interface between stages
<!-- unit:u06 -->
When: Choosing a format for passing data between agent steps; Wanting humans and arbitrary tools to read or modify intermediate artifacts

1. Write all stage handoffs as markdown or JSON files.
2. Avoid binary formats, database connections and proprietary serialization.
3. Keep every artifact openable in a text editor so a human can inspect or modify it.

Boundaries and pitfalls: playbook.md, unit u06.

### Insert a human review gate at every stage boundary
<!-- unit:u07 -->
When: Building a content pipeline (research to script to production) with an AI agent; Errors in early output keep propagating into later stages

1. Split the workflow into discrete stages, each with its own folder and CONTEXT.md. The worked example uses 01_research, 02_script and 03_production.
2. Have each stage read only the previous stage's output folder plus the reference files listed in its CONTEXT.md (e.g. a voice guide and structural template in _config/).
3. Stop after each stage and have the human review the output.
4. Edit the output file directly before the next stage runs, for example by adding a missed research angle or trimming a script that runs too long.
5. Run the next stage on whatever the human left in the previous output folder.

Boundaries and pitfalls: playbook.md, unit u07.

### Scope each stage's context tightly and check it against the token budget
<!-- unit:u08 -->
When: Prompt contains all stage instructions, all reference files and all prior outputs; Model performance degrades or ignores instructions in a long multi-stage workflow

1. For the current stage, count tokens for Layers 0-2 (identity, routing, stage instructions), Layer 3 (references scoped to the stage) and Layer 4 (this run's working material).
2. Compare the total with the typical per-stage range given in the defaults.
3. If the total is far above it, remove material from other stages: their instructions, their reference files and prior outputs already consumed.
4. Condense and structure each stage's output so the next stage's Layer 4 stays small.
5. Prevent bloat by never loading irrelevant layers rather than compressing afterwards.

| Parameter | Value | Tested range | Source |
|---|---|---|---|
| Layers 0-2 combined | roughly 1,300 to 1,600 tokens | - | p. 7 |
| Layer 3 per stage | typically 500 to 2,000 tokens | - | p. 7 |
| Total context per stage | typically 2,000 to 8,000 tokens | - | p. 7 |
| prompt compression token reduction reported by Jiang et al. (alternative to avoidance) | up to 20x with minimal performance loss | - | p. 4 |
| typical ICM context size per stage | 2,000 to 8,000 tokens | described as ICM's typical context sizes; effect of ordering at this scale not tested | p. 15 |

Time-sensitive: check current conditions before reusing these values.

Boundaries and pitfalls: playbook.md, unit u08.

### Audit each stage's context using write, select, compress and isolate
<!-- unit:u09 -->
When: User asks how to structure context for an agent; Stage prompt contains retrieved text, memory, tool notes and prior outputs mixed together

1. Write: author clear instructions for the stage.
2. Select: choose only the context relevant to the stage.
3. Compress: reduce token waste where needed.
4. Isolate: keep unrelated context separate from the stage.
5. Include previous model responses and system state in the review, since they are part of the context.

Boundaries and pitfalls: playbook.md, unit u09.

### Scope tool definitions per stage and layer MCP inside stages
<!-- unit:u10 -->
When: Agent is slow or costly because many tool definitions are loaded upfront; User asks how ICM relates to MCP

1. Treat MCP as the integration layer (how the model reaches tools and data) and the stage folder structure as the context layer (what the agent receives).
2. For each stage, list the tools it actually needs.
3. Load only those tool definitions or MCP connections for that stage, not all tools upfront.
4. Let the stage's folder decide what context accompanies the tool use.

Time-sensitive: check current conditions before reusing these values.

Boundaries and pitfalls: playbook.md, unit u10.

### Configure the factory once, then run the pipeline for each product
<!-- unit:u11 -->
When: Repeating the same kind of deliverable many times; User keeps re-entering brand, style or structure preferences on each run

1. Set up the workspace once with the user's preferences, brand, style and structural decisions, stored as Layer 3 reference files (setup questionnaire, _config/, references/).
2. For each new deliverable, run the pipeline using the same configuration, and put only run-specific content into Layer 4 output/ files.
3. Change the configuration files only when the standing preferences change, not per run.

Boundaries and pitfalls: playbook.md, unit u11.

### Check that a pipeline gives humans visible state and review points
<!-- unit:u12 -->
When: User is designing human oversight for an AI workflow; Users either over-trust or abandon automated outputs

1. Make every intermediate output a readable file, so nothing is hidden between input and output.
2. Define natural breakpoints between stages where a person can invoke, adjust or terminate the process.
3. Make state visible and actions reversible at those breakpoints.
4. Support different levels of automation at different stages, since the right level varies by task.
5. Keep audit trails and defined intervention surfaces for staged review.
6. For regulated high-risk systems, identify which oversight mode applies: human-in-the-loop, human-on-the-loop or human-in-command; treat institutional design as part of oversight, not only technical capability.

Time-sensitive: check current conditions before reusing these values.

Boundaries and pitfalls: playbook.md, unit u12.

### Allocate review effort in a staged pipeline using the U-shaped editing pattern
<!-- unit:u13 -->
When: Deciding where to spend limited human review time in a multi-stage agent workflow; Practitioner asks which stage outputs need the heaviest editing

1. Spend the most deliberate editing effort on stage 1 output (direction-setting). Narrow from broad possibilities to a specific angle.
2. Review middle stages more lightly, provided the earlier output sets direction and Layer 3 reference material (voice guides, templates) constrains execution.
3. Review the final stage heavily as alignment work, checking that the output faithfully reflects earlier decisions.
4. When the final output is misaligned, trace it back through the stage outputs to find where it diverged from the source material.

Boundaries and pitfalls: playbook.md, unit u13.

### Surface the structural plan as an editable file before drafting (course deck workflow)
<!-- unit:u14 -->
When: Producing slide decks or other long artifacts from unstructured source material; An early planning decision determines the whole downstream arc

1. Run five stages in order: content extraction, structural planning, slide drafting, visual design specification, final assembly.
2. Write the structural plan (stage 2 output) as an editable markdown file.
3. Have the human review and correct the plan before any slides are drafted.
4. Only then run drafting and later stages on the approved plan.

Boundaries and pitfalls: playbook.md, unit u14.

### Decide whether to build a new workspace with the builder or duplicate an existing one
<!-- unit:u15 -->
When: Need a workspace for a new domain or content format; Already have a working workspace for a similar format

1. If a similar working workspace exists, duplicate its folder, edit the stage prompts to target the new format, and run it.
2. If none exists, run the workspace-builder: discovery (domain and workflow), stage mapping (natural breakpoints), scaffolding (folder structure), questionnaire design (setup questions), validation (does the pipeline run end to end).
3. Finish by checking that the new workspace runs end to end.

Boundaries and pitfalls: playbook.md, unit u15.

### Tune stage behavior by editing CONTEXT.md in plain text
<!-- unit:u16 -->
When: Output tone or length is off in a particular stage; Non-developer needs to change agent behavior

1. Open the CONTEXT.md of the stage whose behavior needs to change.
2. Adjust tone instructions, add a constraint, or reorder the emphasis in the stage's process description.
3. Re-run the stage and review its output.

| Parameter | Value | Tested range | Source |
|---|---|---|---|
| example length constraint | keep scripts under 90 seconds | - | p. 13 |

Boundaries and pitfalls: playbook.md, unit u16.

### Audit and correct a pipeline run by reading the stage files
<!-- unit:u17 -->
When: Need to see why a pipeline produced a given output; Need an audit trail or defined human intervention points

1. Open the pipeline folder and read the intermediate output files for each stage; no logging layer or dashboard is needed.
2. Correct a stage output by opening the markdown file, editing and saving it.
3. At each review gate, decide whether to proceed, re-run the previous stage with different input, or abandon the run.
4. Keep stage contracts explicit so the capabilities of each stage are clear to reviewers.

Time-sensitive: check current conditions before reusing these values.

Boundaries and pitfalls: playbook.md, unit u17.

### Re-run only the stale stages instead of the whole pipeline
<!-- unit:u18 -->
When: Research output is fine but the script needs rework; A reference file such as a voice guide has changed

1. Identify which file changed (a stage output or a reference file).
2. Open each stage's Inputs table and list the stages that declare the changed file as an input.
3. Treat the outputs of only those stages, and of any stages downstream of them, as possibly stale.
4. Re-run those stages. Leave upstream stages whose inputs did not change untouched.
5. Review the regenerated output at the stage's review gate.

Boundaries and pitfalls: playbook.md, unit u18.

### Add a cross-stage audit that re-checks stage n output against stage n-2
<!-- unit:u19 -->
When: Final-stage output drifts from earlier decisions, such as timing, pacing or revised phrases; Heavy manual editing at the last stage is mostly alignment work

1. Create an audit file for the later stage.
2. In the audit file, instruct the agent to trace back from the stage output to the earlier stage's output, two stages back in the source's example.
3. Have the agent re-read both artifacts and re-verify each item against defined criteria, for example timing for each phrase.
4. Require the agent to flag inconsistencies before the human review gate.
5. Review the flagged discrepancies at the gate and fix them.

Boundaries and pitfalls: playbook.md, unit u19.

### Decide whether to edit an output or fix its source, and treat recurring edits as debugging signals
<!-- unit:u20 -->
When: You keep making the same manual edit to a stage's output; Output tone drifts the same way on every run

1. Before editing a stage output, ask whether this is a one-off human-judgment improvement or a kind of edit you have made before.
2. If it is a one-off improvement the system could not have produced, such as a turn of phrase, edit the output directly and move on.
3. If you keep making the same kind of edit, treat it as a diagnostic signal and trace it back to the source-level file that governs that stage.
4. Fix the source: amend the stage contract with an explicit constraint, or update the reference file, such as adding a stronger example of the target register to the voice guide.
5. Re-run the stage to confirm the recurring edit is no longer needed.

| Parameter | Value | Tested range | Source |
|---|---|---|---|
| Repeat threshold for treating an edit pattern as a source-level problem (proposed for a future ICM version, not an existing feature) | same kind of edit in the same stage's output 3 runs in a row | - | p. 18 |

Boundaries and pitfalls: playbook.md, unit u20.

### Check whether ICM's evidence covers your model and use case before relying on its claims
<!-- unit:u21 -->
When: Considering ICM for a model other than Claude Opus 4.6 or Sonnet 4.6; Expecting proven quality gains over monolithic prompting

1. Confirm which model family you will use. The source tested only Claude Opus 4.6 and Sonnet 4.6.
2. If using another model, treat equivalence as an open empirical question and pilot it on your own workspace before committing.
3. Do not assume scoped context beats monolithic prompting on your task. Run your own comparison on the same task if the difference matters.
4. For academic or policy use, treat the deployments as early-stage.

Time-sensitive: check current conditions before reusing these values.

Boundaries and pitfalls: playbook.md, unit u21.

## Going deeper
- Boundaries, pitfalls and worked examples per unit: playbook.md
- Evidence with page cites and the extracted-unit ids behind each unit: references/evidence.md
- Provenance (source hash, unit lineage): references/provenance.json

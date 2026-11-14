# Playbook: folder-structured-agent-workflows

Use when designing, setting up, or debugging a sequential, multi-stage AI agent workflow with human review between stages, for example when a user asks to 'organize an agent pipeline as folders', 'replace a multi-agent framework with files', 'write stage contracts or CONTEXT.md files', or 'control what context each step sees'. Applies a folder-as-architecture method: numbered stage folders, layered context loading, plain-file handoffs and review gates. Not for workflows needing real-time multi-agent collaboration, high concurrency, or fully autonomous operation without human review.

This is a procedure: once the fit check passes, follow the matching unit's steps in order.

Source: *Interpretable Context Methodology: Folder Structure as Agentic Architecture* by Jake Van Clief; David McDermott (file icm-2603.16021v2.pdf). Page cites such as (p. N) refer to that document. They are for checking this skill; cite them in an answer only when the user asks or a number is decisive, and then name the document in plain words.

### Check whether a workflow fits the folder-per-stage (ICM) design before adopting it
<!-- unit:u01 -->
When: Deciding between ICM (folder-based staged pipeline) and a multi-agent framework such as AutoGen; User describes a repeatable multi-step AI workflow and asks what architecture to use; Considering scaling a local ICM pipeline to many users or automating mid-pipeline branching; Choosing between a folder-based workspace and an agent orchestration framework; Evaluating whether a multi-step AI workflow needs a framework, server, or developer; Planning to build a new ICM workspace for some domain; User is choosing between a folder-based pipeline and an agent framework such as LangChain, AutoGen or CrewAI; User asks whether a multi-step AI workflow needs orchestration code; User wants a human-reviewed sequential content or research pipeline; User is choosing between a framework (CrewAI, LangChain, AutoGen) and a lighter approach for an agent workflow; User finds that reordering steps, swapping a prompt, or skipping a stage means editing code and redeploying; User's workflow is sequential and a human reviews output at each step; Choosing between a file-and-folder workflow and a code framework that orchestrates agents; Evaluating whether the approach suits a given project

1. Test the workflow on three properties: sequential (step 2 follows step 1), reviewable (a human should check each step's output), repeatable (the same pipeline runs repeatedly, e.g. weekly or daily, with different input).
2. If all three hold, use ICM: stage folders and file handoffs, with no framework code, server infrastructure or developer dependency for day-to-day operation.
3. Check the exclusions: do agents need to talk to each other dynamically in tight loops? Do many users hit the same pipeline at once? Must the AI itself decide branching mid-pipeline?
4. If any exclusion applies, do not use ICM for that part. Use a multi-agent or queueing framework instead.
5. If branching is needed but a human can decide, keep ICM and have the human choose the next stage between stages (for example run stage 3a instead of 3b after reading the stage 2 output).

Boundaries (where the source says this held; re-check before applying):
- Fits: sequential multi-step workflows where a human reviews output at each stage and the same pipeline runs repeatedly with different input.
- Reported deployments: content production (script-to-animation, short-form video), training material (slide decks from source material), academic research workflows, policy analysis.
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
- Do NOT apply it for concurrent execution or native parallel agent coordination.
- Do NOT apply it for heavy external service integration through programmatic API calls and auth management; the folder approach offers only local scripts or MCP connections.
- The authors say frameworks work well for dynamic multi-agent collaboration, concurrent execution or complex branching logic.
- The comparison is for sequential, human-reviewed workflows.
- Fits: sequential workflows where a human reviews output at each step.
- Frameworks are described as working well for complex, concurrent systems; the authors do not claim ICM replaces them there.
- Frameworks are described as working within their own structures. Changing step order, a prompt, or stages typically requires editing code, understanding abstractions, and redeploying.
- This section is an introduction and gives no measured comparison, so the fit criterion is the authors' position, not a tested result.
- Do not apply when you need the flexibility of a programmatic orchestrator; the source states ICM gives that up deliberately.
- Applies where stage-to-stage handoff by files is acceptable; the source's example pipelines are sequential.

Pitfalls:
- Forcing ICM onto concurrent or real-time multi-agent use means rebuilding the infrastructure ICM was designed to avoid.
- Adding automated branching scripts gradually turns ICM into an ad hoc framework.
- Choosing a heavy framework for a simple sequential reviewable pipeline brings opacity, fragility, developer dependency and slower iteration.
- Applying the approach to workflows that are not sequential, reviewable, and repeatable and expecting the same benefits.
- Adding an orchestration framework or server for a workflow that already fits the folder model.
- Adopting a framework for a purely sequential, human-reviewed pipeline adds a coordination layer that may not be needed.
- Forcing branching, parallelism or automated recovery into folders and manual re-runs where the task needs them.
- Adopting a full framework for a sequential, human-reviewed workflow adds engineering overhead the problem does not require.
- Adopting a folder-based approach for concurrent, complex systems goes against the scope the authors describe (extrapolation: likely to be a poor fit).
- Expecting the folder approach to give orchestrator-level flexibility.

Evidence behind this unit:
- Grade C (practitioner heuristic): ICM has been applied to sequential, human-reviewed, repeatable workflows in content production, training material, academic research and policy analysis; its unsuitable cases are real-time multi-agent, high-concurrency and automated-branching systems. (p. 14). Conditions: Authors' description of their own deployments and design boundaries; no controlled comparison reported in this section.
- Grade C (practitioner heuristic): The authors claim that for practitioners whose AI workflows are sequential, reviewable, and repeatable, ICM gives full pipeline capability with no framework to learn, no server to maintain, and no developer needed for day-to-day operation. (p. 18). Conditions: The authors' concluding claim; this section reports no measurements. It holds for the stated workflow class only.
- Grade C (practitioner heuristic): For sequential, human-reviewed workflows, the folder approach simplifies six common operations, while frameworks provide error recovery, conditional branching, concurrency and richer service integration that the folder approach lacks or handles less well. (p. 2). Conditions: Author-built qualitative comparison table; no measurements; sequential, human-reviewed workflows.
- Grade C (practitioner heuristic): For sequential workflows, frameworks solve a coordination problem that may not need to exist, since the same coordination can be done with files in folders. (p. 3). Conditions: Authors' argument for sequential workflows only; they say frameworks work well for dynamic multi-agent collaboration, concurrency or complex branching.
- Grade C (practitioner heuristic): Frameworks suit complex, concurrent systems but add engineering overhead for sequential, human-reviewed workflows; for these the control surface can be much simpler. (p. 1). Conditions: Authors' framing in the abstract and introduction; no data or experiment is presented in this section.
- Grade C (practitioner heuristic): ICM trades the flexibility of a programmatic orchestrator for the portability, inspectability and editability of plain files. (p. 8). Conditions: Authors' stated design tradeoff, supported by an appeal to Gabriel and Plan 9; not tested.
Inference (not stated in the source): Workflows that are non-sequential, not human-reviewable, or one-off are inferred to be a poor fit. The source states only the fit condition, not the converse.
Inference (not stated in the source): The newsletter scenario and the hybrid suggestion are illustrative applications, not stated in the source.
Inference (not stated in the source): Advice to prefer file edits when the workflow changes often is inferred from the authors' complaint about editing code; it is not stated as a rule.
Inference (not stated in the source): What kinds of workflows (branching, parallel) exceed the folder approach is inferred from the stated flexibility tradeoff; the source does not enumerate them.

### Organize an agent workspace as numbered stage folders with a five-layer context hierarchy
<!-- unit:u02 -->
When: Designing a multi-step agent workflow and deciding how to give each step its context; Agent prompts keep growing as stages and reference files are added; User asks how to structure a folder so an agent knows where it is and what to load; User wants to orchestrate a multi-step AI workflow without building a coordination framework; User wants to inspect and edit what context the agent gets at each stage; User has prompts and context for each stage already written as files

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

Boundaries (where the source says this held; re-check before applying):
- Token sizes are the authors' representative figures, not tested ranges.
- The example workspace is a three-stage, sequential pipeline (research, script, production). Fit to non-sequential or branching workflows is not addressed.
- Larger reference collections can include their own routing CONTEXT.md inside a configuration or design-system folder, which applies the Layer 1 routing pattern recursively within Layer 3.
- Applies to sequential workflows with human review at each step, per the authors' scope.
- The section gives no file naming conventions, folder schemas, or tested limits; those are not specified here.
- The authors say the method draws on Unix pipeline design, modular decomposition, multi-pass compilation, and literate programming.

Pitfalls:
- Letting an agent load everything in the workspace.
- Letting the agent decide by its own judgment what matters, without explicit scoping.
- Loading every layer for every stage, which defeats the design.
- Leaving mechanical tasks (fetching, moving files, formatting, emailing) to the AI instead of scripts adds work the authors say does not need AI.
- Prompts and context kept outside the folder hierarchy undercut the central premise that the files tell the agent what to do at each step.

Evidence behind this unit:
- Grade C (practitioner heuristic): The five-layer hierarchy with approximate token sizes per layer; no agent reads everything, which keeps token cost low and context focused. (p. 6). Conditions: Authors' architecture description; no controlled comparison in this section.
- Grade C (practitioner heuristic): If each stage's prompts and context already exist as files in a well-organized folder hierarchy, a coordination framework is not needed; one agent reading the right files at the right moment suffices. (p. 1). Conditions: Stated as the authors' central observation; no empirical test is reported in this section.
Inference (not stated in the source): Applying the layout to non-video workflows such as newsletters is an extrapolation; the source's example is a script-to-animation workspace.
Inference (not stated in the source): The example folder names and the sample workflow are illustrative, not from the source.
Inference (not stated in the source): The 'edit files to change workflow' step is inferred from the authors' contrast with editing code.

### Write each stage as a contract with Inputs, Process and Outputs
<!-- unit:u03 -->
When: Creating or revising a stage's CONTEXT.md; An agent loads too much or the wrong files for a step; Need the pipeline to be auditable and self-documenting

1. In the stage's CONTEXT.md, write an Inputs section that lists exactly which files to load, and which sections of them if only part is relevant.
2. Label each input as Layer 4 (working, from the previous stage's output/ folder) or Layer 3 (reference, such as _config/voice.md or references/structure.md).
3. Write a Process section with short instructions that point to the reference files, e.g. follow the structure in one file and match the tone in another.
4. Write an Outputs section naming each file and the output/ folder it is written to.
5. Have the agent read the CONTEXT.md, follow it, and write the output.
6. Let the next stage read whatever is in the output folder, including human edits.

Boundaries (where the source says this held; re-check before applying):
- Stage sequencing comes from folder numbering, context scoping from the folder hierarchy, state from files on disk.
- Each stage reads from the previous stage's output folder and writes to its own.

Pitfalls:
- Without an explicit Inputs table, the agent loads everything or relies on its own judgment about what matters.
- Letting a stage load files outside its Inputs list.

Evidence behind this unit:
- Grade C (practitioner heuristic): The Inputs table makes context selection explicit, editable and auditable, and makes Layer 2 the control point of the system. (p. 7). Conditions: Authors' design argument; no measurements in this section.
- Grade C (practitioner heuristic): Typical contract has three parts (inputs, process, outputs), and the instruction files double as documentation so a new team member can read them top to bottom. (p. 9). Conditions: Illustrated with one example script-stage contract.

### Separate reference material (Layer 3) from working artifacts (Layer 4)
<!-- unit:u04 -->
When: Persistent rules (voice, design system, conventions) and per-run content are mixed in one prompt or file; Setting up a workspace that will be run repeatedly; Deciding where to put a new file; A stage prompt mixes style rules and input data in one block; Model ignores style or format guidelines; Setting up Layer 3 and Layer 4 files for a stage

1. For each file ask: does it change between runs? If no, it is Layer 3 reference. If yes, it is Layer 4 working artifact.
2. Put Layer 3 files (e.g. voice.md, design-system.md, conventions.md) in references/, _config/ or shared/, and configure them once during workspace setup.
3. Put Layer 4 files (e.g. research-output.md, script-draft.md) in the stage output/ folders. They are produced during each pipeline run.
4. In stage instructions, tell the model to internalize Layer 3 as constraints and to process Layer 4 as input to transform.
5. Never store per-run content in the reference folders or persistent rules in output/.

Boundaries (where the source says this held; re-check before applying):
- Layer 3 is configured at workspace setup (once); Layer 4 during pipeline execution (each run).
- The source describes the separation as helping the model receive pre-organized context; it gives no measured effect size.
- Whether this separation measurably improves output quality versus a flat context of equivalent content is an open empirical question.
- Support is early practitioner experience only, on a single model family.

Pitfalls:
- Mixing persistent rules with per-run artifacts in an undifferentiated context window forces the model to sort them itself.
- Treating reference rules as input to transform, or treating source material as constraints.
- Mixing rules and input in a flat prompt gives the model unclear signals about what constrains it and what it should act on.

Evidence behind this unit:
- Grade C (practitioner heuristic): Layer 3 is stable, internalized as constraints, and lives in references/, _config/, shared/. Layer 4 changes every run, is processed as input, and lives in output/. (p. 6). Conditions: Design rationale from the authors; no experiment reported in this section.
- Grade C (practitioner heuristic): Stages where reference and working material are clearly separated produced more consistent adherence to style and format guidelines. (p. 15). Conditions: Early practitioner experience, not a controlled comparison; flat-context benefit untested.

### Give each stage exactly one job and a readable input and output
<!-- unit:u05 -->
When: A stage's instructions cover several different operations; Debugging which step produced a bad result; Planning how to split a workflow into stages; User is designing a multi-step AI workflow; One stage prompt is doing research, filtering and writing at once; Intermediate results are hard to inspect or replace

1. List the workflow's steps and assign each to one stage folder.
2. Check that each stage does only one thing; for example a stage that fetches data does not also filter it, and a stage that filters does not also format the final output.
3. Define for each stage a specific input it reads and a specific output it writes to its own folder.
4. If a stage does two jobs, split it into two stages.

Boundaries (where the source says this held; re-check before applying):
- Rationale is borrowed from McIlroy's Unix principle and Parnas's information-hiding criterion and compares stages to compiler passes; no empirical test is given here.
- The principles come from Unix, pipe-and-filter, Make and compiler design; applying them to AI agent workflows is the authors' framing.
- The source frames this as a fit for sequential workflows; branching and parallel designs are not covered here.

Pitfalls:
- Combining fetch, filter and format in one stage, which removes clean review points and blurs responsibility.
- Monolithic stages cannot be inspected, replaced or tested independently.
- Opaque or non-text interfaces between stages defeat inspection and debugging.

Evidence behind this unit:
- Grade C (practitioner heuristic): Each stage handles a single workflow step and writes to its own folder, reading a defined input and writing a defined output. (p. 5). Conditions: Design principle justified by analogy to established software practice.
- Grade C (practitioner heuristic): Unix design principles: do one thing well, make every output usable as another's input, and use text streams as the universal interface. (p. 2). Conditions: Historical design principles from McIlroy (1978); not an empirical test on AI workflows.
- Grade C (practitioner heuristic): In the pipe-and-filter pattern any component can be replaced, inspected or tested independently. (p. 3). Conditions: Architectural claim of Shaw and Garlan as cited; no measurements.
Inference (not stated in the source): Mapping each principle to specific file-naming conventions is not in the source.

### Use plain text files as the interface between stages
<!-- unit:u06 -->
When: Choosing a format for passing data between agent steps; Wanting humans and arbitrary tools to read or modify intermediate artifacts

1. Write all stage handoffs as markdown or JSON files.
2. Avoid binary formats, database connections and proprietary serialization.
3. Keep every artifact openable in a text editor so a human can inspect or modify it.

Boundaries (where the source says this held; re-check before applying):
- The source excludes binary formats and databases for stage communication; it does not discuss data that is inherently binary.

Pitfalls:
- Proprietary or binary intermediates that only specific tools can read, which breaks inspection and editing.

Evidence behind this unit:
- Grade C (practitioner heuristic): Any tool that reads a text file can participate in the workflow, and any human with a text editor can inspect or modify any artifact. (p. 5). Conditions: Argument from Kernighan and Pike's text-as-universal-interface; no measurements.
Inference (not stated in the source): Large binary assets (images, video) are not covered by the source; handling them alongside text handoffs is not specified.

### Insert a human review gate at every stage boundary
<!-- unit:u07 -->
When: Building a content pipeline (research to script to production) with an AI agent; Errors in early output keep propagating into later stages; User asks how to structure a multi-step agent workflow; A multi-stage agent pipeline where errors in early stages propagate; User wants to correct intermediate results without rerunning everything; Need transparency into what each step produced

1. Split the workflow into discrete stages, each with its own folder and CONTEXT.md. The worked example uses 01_research, 02_script and 03_production.
2. Have each stage read only the previous stage's output folder plus the reference files listed in its CONTEXT.md (e.g. a voice guide and structural template in _config/).
3. Stop after each stage and have the human review the output.
4. Edit the output file directly before the next stage runs, for example by adding a missed research angle or trimming a script that runs too long.
5. Run the next stage on whatever the human left in the previous output folder.

Boundaries (where the source says this held; re-check before applying):
- Worked example is a 3-stage script-to-animation pipeline run in a single Claude Code session with one orchestrating agent (Opus 4.6) delegating to Sonnet 4.6 sub-agents.
- All testing used a single model family (Claude Opus 4.6 and Sonnet 4.6); other models may differ.
- Most active use is content production; academic and policy deployments are early-stage.
- No controlled comparison against monolithic prompting has been run.
- Output formats are plain text (markdown or JSON); no binary formats, databases or proprietary serialization.
- The same model executes every stage; only the context differs through the folder structure.

Pitfalls:
- Skipping review lets a missed angle or an overlong script flow downstream unchanged.
- Letting a later stage read raw upstream material instead of the reviewed output defeats the gate.
- Opaque binary or database intermediate state that humans cannot inspect or edit.
- Running stages back-to-back with no review point, so human edits cannot be picked up.

Evidence behind this unit:
- Grade C (practitioner heuristic): In the script-to-animation workspace, the human reviews and edits the output at each stage boundary, and the next stage works with whatever the human left. (p. 11). Conditions: Author-built workspace, single Claude Code session, Claude Opus 4.6 and Sonnet 4.6; descriptive account, not a controlled test.
- Grade C (practitioner heuristic): Each stage boundary lets the human inspect and edit the output before the next stage runs, and the next stage picks up the edited file. (p. 8). Conditions: Design description (mixed-initiative and direct-manipulation framing); no user study in this section.
Inference (not stated in the source): Applying the gate pattern to non-media workflows such as newsletters is an extrapolation from the script-to-animation example.

### Scope each stage's context tightly and check it against the token budget
<!-- unit:u08 -->
When: Prompt contains all stage instructions, all reference files and all prior outputs; Model performance degrades or ignores instructions in a long multi-stage workflow; Deciding how much to load per stage; Agent quality degrades as a multi-stage workflow accumulates context; User is loading every document and prior output into one long context window; User asks whether to compress prompts or avoid loading context; Stage output is inconsistent in style or format; A stage prompt has open-ended instructions and large volumes of reference material; Designing a new pipeline stage's folder contents

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

Boundaries (where the source says this held; re-check before applying):
- Counts come from a representative script-to-animation workspace with three stages; other domains may differ.
- Layer 4 'rarely exceeds a few thousand tokens' only when the previous stage has condensed and structured its output.
- The monolithic estimate of 30,000 to 50,000 tokens (about 42k in the figure) is an illustrative estimate, not a benchmark run.
- The cited evidence concerns relevant information buried in the middle of long contexts.
- The authors present stage-specific loading as simpler than compression, but give no head-to-head comparison.
- The source gives no threshold for how much context is too much.
- Evidence is early practitioner experience, not a controlled study.
- All current testing was on a single model family; generalization across Claude, GPT, Gemini or Llama is untested (future work).
- If models reliably attend to very large contexts (the paper's example is 200,000 tokens without degradation), the engineering argument for scoping weakens. The human-interaction arguments (observability, editability, review gates) remain.
- Whether the order or formatting of files within a layer matters is untested; the protocol does not prescribe ordering.

Pitfalls:
- Loading all stages' material, which reaches 30,000 to 50,000 tokens and where cited work (Liu et al.) found significant performance degradation on information-retrieval tasks.
- Unused context occupying space without contributing to the current task.
- Dumping all stage files into one context buries relevant information and lowers performance on the material that matters.
- Compressing irrelevant context after loading it treats the problem after the fact.
- Broad, loosely defined stage context gives less consistent results.
- Loading everything into every stage defeats the scoping mechanism.

Evidence behind this unit:
- Grade C (practitioner heuristic): Representative token counts from one script-to-animation workspace: each of three ICM stages delivers 2,000-8,000 focused tokens, versus a monolithic prompt of about ~42k tokens in the figure (the text says such a prompt can easily reach 30,000 to 50,000). (p. 8). Conditions: Representative token counts from one script-to-animation workspace; no model-accuracy comparison reported here.
- Grade B (observational or case study): LLMs perform significantly worse when relevant information is buried in the middle of long contexts, and more irrelevant material in the window means worse performance on the material that matters. (p. 4). Conditions: Finding from Liu et al., cited secondhand in this paper; no numbers given; long contexts.
- Grade C (practitioner heuristic): Stages with tightly scoped context (clear instructions, limited reference material, specific output format) produced more consistent results than stages with broad context. (p. 15). Conditions: Early practitioner pattern in ICM use on one model family; no controlled comparison.

Time-sensitive: check current conditions before reusing these values.
Inference (not stated in the source): The statement that these sizes are 'well within the range where current models perform at their best' depends on current models; check against the model you use.
Inference (not stated in the source): The advice to reference only the needed files from the stage instructions is an implementation detail not stated in the source.
Inference (not stated in the source): Narrowing context before changing the model is a practical inference from the stated pattern, not a claim in the source.

### Audit each stage's context using write, select, compress and isolate
<!-- unit:u09 -->
When: User asks how to structure context for an agent; Stage prompt contains retrieved text, memory, tool notes and prior outputs mixed together

1. Write: author clear instructions for the stage.
2. Select: choose only the context relevant to the stage.
3. Compress: reduce token waste where needed.
4. Isolate: keep unrelated context separate from the stage.
5. Include previous model responses and system state in the review, since they are part of the context.

Boundaries (where the source says this held; re-check before applying):
- This is a practitioner taxonomy (Lance Martin) and the source gives no quantitative thresholds.
- Context here means instructions, retrieved knowledge, memory, tool descriptions and prior outputs.

Pitfalls:
- Treating context engineering as crafting a single prompt.
- Ignoring previous model responses and system state, which also fill the context.

Evidence behind this unit:
- Grade C (practitioner heuristic): Context engineering strategies can be organized as write, select, compress and isolate. (p. 3). Conditions: Practitioner taxonomy from LangChain as cited; not experimentally validated here.

### Scope tool definitions per stage and layer MCP inside stages
<!-- unit:u10 -->
When: Agent is slow or costly because many tool definitions are loaded upfront; User asks how ICM relates to MCP; A stage needs external services

1. Treat MCP as the integration layer (how the model reaches tools and data) and the stage folder structure as the context layer (what the agent receives).
2. For each stage, list the tools it actually needs.
3. Load only those tool definitions or MCP connections for that stage, not all tools upfront.
4. Let the stage's folder decide what context accompanies the tool use.

Boundaries (where the source says this held; re-check before applying):
- The source gives a qualitative observation only, with no measured speed or cost figures.
- MCP and ICM are described as complementary, not alternatives.

Pitfalls:
- Loading all tool definitions into the context window upfront slows agents and increases costs.
- Treating MCP as a substitute for stage-level context structuring.

Evidence behind this unit:
- Grade C (practitioner heuristic): Loading all tool definitions upfront slows agents and increases costs; stage-scoped tool definitions avoid this. (p. 4). Conditions: Observation attributed to Jones and Kelly at Anthropic; no numbers; the avoidance benefit is the authors' argument.

Time-sensitive: check current conditions before reusing these values.

### Configure the factory once, then run the pipeline for each product
<!-- unit:u11 -->
When: Repeating the same kind of deliverable many times; User keeps re-entering brand, style or structure preferences on each run

1. Set up the workspace once with the user's preferences, brand, style and structural decisions, stored as Layer 3 reference files (setup questionnaire, _config/, references/).
2. For each new deliverable, run the pipeline using the same configuration, and put only run-specific content into Layer 4 output/ files.
3. Change the configuration files only when the standing preferences change, not per run.

Boundaries (where the source says this held; re-check before applying):
- Best suited to repeatable production pipelines; one-off tasks gain less.

Pitfalls:
- Re-specifying style and structure in every run, which causes drift between deliverables.
- Embedding per-run content in the configuration files.

Evidence behind this unit:
- Grade C (practitioner heuristic): Workspace is configured once; each run produces a new deliverable with the same configuration, following continuous-delivery repeatability. (p. 5). Conditions: Design principle; no repeatability data in this section.

### Check that a pipeline gives humans visible state and review points
<!-- unit:u12 -->
When: User is designing human oversight for an AI workflow; Users either over-trust or abandon automated outputs; User asks about the EU AI Act or audit trails for high-risk AI; User asks how to make a pipeline interpretable

1. Make every intermediate output a readable file, so nothing is hidden between input and output.
2. Define natural breakpoints between stages where a person can invoke, adjust or terminate the process.
3. Make state visible and actions reversible at those breakpoints.
4. Support different levels of automation at different stages, since the right level varies by task.
5. Keep audit trails and defined intervention surfaces for staged review.
6. For regulated high-risk systems, identify which oversight mode applies: human-in-the-loop, human-on-the-loop or human-in-command; treat institutional design as part of oversight, not only technical capability.

Boundaries (where the source says this held; re-check before applying):
- The regulatory point concerns high-risk AI systems under the EU AI Act as described by the authors; it is not legal advice.
- The source gives no quantitative thresholds for oversight design.
- Rudin's argument is for inherently interpretable systems; here applied at the workflow level, not the model level.

Pitfalls:
- Opaque outputs lead people to trust blindly (misuse) or stop using the system (disuse).
- Explaining an opaque pipeline after the fact instead of making it inspectable.
- Technical capability for oversight without institutional design.

Evidence behind this unit:
- Grade B (observational or case study): Opaque automated outputs lead to misuse or disuse, both because the human cannot see what happened between input and output. (p. 4). Conditions: Parasuraman and Riley, cited secondhand; qualitative; automation in general, not specifically LLM workflows.
- Grade B (observational or case study): Systems should let users invoke, adjust and terminate automated processes at natural breakpoints, which requires visible state and reversible actions. (p. 4). Conditions: Horvitz mixed-initiative principles, cited secondhand; qualitative.

Time-sensitive: check current conditions before reusing these values.
Inference (not stated in the source): The sign-off step in the example is an illustrative application; the source does not prescribe it.
Inference (not stated in the source): Regulatory suitability of any specific pipeline is not established by the source.

### Allocate review effort in a staged pipeline using the U-shaped editing pattern
<!-- unit:u13 -->
When: Deciding where to spend limited human review time in a multi-stage agent workflow; Practitioner asks which stage outputs need the heaviest editing; Final output drifts from decisions made earlier

1. Spend the most deliberate editing effort on stage 1 output (direction-setting). Narrow from broad possibilities to a specific angle.
2. Review middle stages more lightly, provided the earlier output sets direction and Layer 3 reference material (voice guides, templates) constrains execution.
3. Review the final stage heavily as alignment work, checking that the output faithfully reflects earlier decisions.
4. When the final output is misaligned, trace it back through the stage outputs to find where it diverged from the source material.

Boundaries (where the source says this held; re-check before applying):
- Based on 33 community members using the script-to-animation workspace or similar multi-stage workspaces. 30 reported a U-shape and 3 reported roughly equal editing across all stages.
- Values are practitioner self-report through conversation, not instrumented measurement.
- The community is invite-only and self-selected, so selection and enthusiasm bias are possible.
- Light middle-stage review is justified only when both anchors exist: earlier stage output and reference material. Without them, no basis is given for trusting the middle stages.
- Section 6 is said to explore traceability tooling; none is described here.
- This changes review DEPTH, not whether a gate exists: keep a review gate at every stage boundary (the paper's pipeline figure shows one after each stage, p. 9). Middle stages get a lighter touch only when the earlier output and the reference files anchor them (p. 12).

Pitfalls:
- Treating middle stages as trusted when no reference material constrains them.
- Treating final-stage edits as creative rewrites rather than debugging back to the source decisions.
- Reading the 30 of 33 figure as measured effect rather than self-report.

Evidence behind this unit:
- Grade C (practitioner heuristic): 30 of 33 practitioners reported heavy editing at stage 1, light editing in the middle stages, and heavy editing again at the final stage; 3 reported roughly equal editing across stages. (p. 12). Conditions: Self-report through conversations with an invite-only community; script-to-animation or structurally similar multi-stage workspaces; not instrumented.
Inference (not stated in the source): The advice to skim middle stages only when both anchors exist is the source's explanation of why practitioners trust them, restated as a condition.

### Surface the structural plan as an editable file before drafting (course deck workflow)
<!-- unit:u14 -->
When: Producing slide decks or other long artifacts from unstructured source material; An early planning decision determines the whole downstream arc; Need to decide where human judgment matters most in a pipeline

1. Run five stages in order: content extraction, structural planning, slide drafting, visual design specification, final assembly.
2. Write the structural plan (stage 2 output) as an editable markdown file.
3. Have the human review and correct the plan before any slides are drafted.
4. Only then run drafting and later stages on the approved plan.

Boundaries (where the source says this held; re-check before applying):
- Described for course deck production from PDFs, papers, lecture notes and rough outlines.
- No quantitative evidence is given for this workspace.
- The reasoning is that errors in the structural plan make everything downstream wrong.

Pitfalls:
- Drafting slides before the plan is approved means a wrong arc invalidates all downstream work.

Evidence behind this unit:
- Grade C (practitioner heuristic): Exposing the structural plan as an editable file lets the human correct it at the cheapest point, before slides are drafted. (p. 11). Conditions: Qualitative description of the author's course deck workspace; no measurements.

### Decide whether to build a new workspace with the builder or duplicate an existing one
<!-- unit:u15 -->
When: Need a workspace for a new domain or content format; Already have a working workspace for a similar format; Non-expert wants to create a workspace without learning the conventions

1. If a similar working workspace exists, duplicate its folder, edit the stage prompts to target the new format, and run it.
2. If none exists, run the workspace-builder: discovery (domain and workflow), stage mapping (natural breakpoints), scaffolding (folder structure), questionnaire design (setup questions), validation (does the pipeline run end to end).
3. Finish by checking that the new workspace runs end to end.

Boundaries (where the source says this held; re-check before applying):
- Duplication is reported as the common practice, e.g. from short explainer videos to long-form essays, though the builder supports creating from nothing.
- Builder-created workspaces are claimed to stay consistent because the builder follows the same structural rules.
- Evidence is practitioner report only; 3 community members with no coding experience reportedly built workspaces that produced ten-minute animated videos (single small group).
- External adoption details are limited by nondisclosure agreements.

Pitfalls:
- Rebuilding from scratch when a close workspace exists wastes effort.
- Duplicating without updating all stage prompts leaves the old format's behavior in the new workspace.

Evidence behind this unit:
- Grade C (practitioner heuristic): In practice people often prefer to copy and adapt an existing workspace rather than start from a blank one. (p. 13). Conditions: Informal community observations from an invite-only group; limited set of workflow types.
- Grade C (practitioner heuristic): The workspace-builder is a five-stage workspace (discovery, stage mapping, scaffolding, questionnaire design, validation) whose output is a new workspace. (p. 11). Conditions: Descriptive account of the tool by its authors.

### Tune stage behavior by editing CONTEXT.md in plain text
<!-- unit:u16 -->
When: Output tone or length is off in a particular stage; Non-developer needs to change agent behavior; Need to add a constraint to one stage

1. Open the CONTEXT.md of the stage whose behavior needs to change.
2. Adjust tone instructions, add a constraint, or reorder the emphasis in the stage's process description.
3. Re-run the stage and review its output.

| Parameter | Value | Tested range | Source |
|---|---|---|---|
| example length constraint | keep scripts under 90 seconds | - | p. 13 |

Boundaries (where the source says this held; re-check before applying):
- Reported by practitioners including non-technical users; informal community reports, not a controlled study.
- The 90-second figure is an example of a constraint users added, not a tested optimum.
- Equivalent to modifying agent configuration in a framework-based system.

Pitfalls:
- Editing the generated output instead of the stage's CONTEXT.md means the same issue recurs on the next run.

Evidence behind this unit:
- Grade C (practitioner heuristic): Non-technical users successfully modified stage behavior by editing markdown CONTEXT.md files (tone, constraints, emphasis). (p. 13). Conditions: Informal practitioner reports from an invite-only community of 52 members; no formal data collection.
Inference (not stated in the source): The example uses tone and length constraints, which the source names only as categories of edits.

### Audit and correct a pipeline run by reading the stage files
<!-- unit:u17 -->
When: Need to see why a pipeline produced a given output; Need an audit trail or defined human intervention points; A stage's output is wrong and must be fixed or rejected

1. Open the pipeline folder and read the intermediate output files for each stage; no logging layer or dashboard is needed.
2. Correct a stage output by opening the markdown file, editing and saving it.
3. At each review gate, decide whether to proceed, re-run the previous stage with different input, or abandon the run.
4. Keep stage contracts explicit so the capabilities of each stage are clear to reviewers.

Boundaries (where the source says this held; re-check before applying):
- Observability comes from intermediate outputs being plain text files; it depends on every stage handing off through files.
- Whether this satisfies EU AI Act human oversight requirements is a legal question the paper does not answer; only structural alignment (staged review, audit trails, defined intervention points) is noted.

Pitfalls:
- Treating the folder structure as proof of regulatory compliance overstates the source's claim.
- Skipping review gates removes the dismissal and correction options.

Evidence behind this unit:
- Grade C (practitioner heuristic): Because every intermediate output is a plain file, the system is observable by default; stage contracts, editable markdown and review gates map to Amershi et al.'s guidelines on clarity, correction and dismissal. (p. 14). Conditions: Authors' architectural argument; no user study reported in this section.

Time-sensitive: check current conditions before reusing these values.

### Re-run only the stale stages instead of the whole pipeline
<!-- unit:u18 -->
When: Research output is fine but the script needs rework; A reference file such as a voice guide has changed; Unsure which stage outputs are out of date after an edit

1. Identify which file changed (a stage output or a reference file).
2. Open each stage's Inputs table and list the stages that declare the changed file as an input.
3. Treat the outputs of only those stages, and of any stages downstream of them, as possibly stale.
4. Re-run those stages. Leave upstream stages whose inputs did not change untouched.
5. Review the regenerated output at the stage's review gate.

Boundaries (where the source says this held; re-check before applying):
- The source describes this as supported by default in ICM workspaces. Dependencies are tracked implicitly through each stage's Inputs table, not by tooling.
- The source's example workspace is a research, script, production pipeline. No other regime is tested.
- A changed input only signals that output may be stale. It does not prove the output is wrong.
- The source says future work on dependency tracking and change propagation is still needed.
- Treat re-running as a manual practice based on each stage's Inputs table. Automatic dependency tracking and change propagation are the authors' proposed future work, not implemented tooling.

Pitfalls:
- An Inputs table that omits a file the stage actually reads hides a dependency, so a stale output is not flagged.
- Rebuilding everything from scratch wastes work and can overwrite approved upstream output.

Evidence behind this unit:
- Grade C (practitioner heuristic): ICM supports incremental re-running: a practitioner re-runs stage 2 without touching stage 1, and a changed voice guide triggers only the stages that load it. (p. 16). Conditions: Practitioner description of the ICM script-to-animation workspace. The compiler analogy is the authors' framing and no controlled test is reported.
Inference (not stated in the source): The step of also treating downstream stages as possibly stale follows from the pipeline structure. The source does not state it explicitly.

### Add a cross-stage audit that re-checks stage n output against stage n-2
<!-- unit:u19 -->
When: Final-stage output drifts from earlier decisions, such as timing, pacing or revised phrases; Heavy manual editing at the last stage is mostly alignment work; Output references text that was revised upstream

1. Create an audit file for the later stage.
2. In the audit file, instruct the agent to trace back from the stage output to the earlier stage's output, two stages back in the source's example.
3. Have the agent re-read both artifacts and re-verify each item against defined criteria, for example timing for each phrase.
4. Require the agent to flag inconsistencies before the human review gate.
5. Review the flagged discrepancies at the gate and fix them.

Boundaries (where the source says this held; re-check before applying):
- The audit file is a production practice in the script-to-animation workspace. The source says it catches most alignment errors but gives no rates.
- The errors it catches are consistent in kind: frame count discrepancies, visual density mismatches, and pacing breaks at scene boundaries.
- Putting a Verify section in every stage contract is a proposed generalization. The source says it is not yet implemented.
- The source does not report testing the audit in domains other than script-to-animation.

Pitfalls:
- Without a trace-back check, misalignment between the specification and the script goes unnoticed until human review.
- The check is only as good as its criteria. Vague criteria give weak verification.

Evidence behind this unit:
- Grade C (practitioner heuristic): The authors report that an audit file forcing the agent to trace the specification back to the original script and re-verify timing per phrase catches most alignment errors. The authors call it a proto-debugger. (p. 17). Conditions: Practitioner observation in the script-to-animation workspace. No quantitative rate is given.
Inference (not stated in the source): Applying the audit to non-animation workspaces such as slide decks is an extrapolation from the source's single example workspace.

### Decide whether to edit an output or fix its source, and treat recurring edits as debugging signals
<!-- unit:u20 -->
When: You keep making the same manual edit to a stage's output; Output tone drifts the same way on every run; You are about to hand-fix an output and want to know whether the fix will last; Creative output that needs a human touch; A script or other stage output sounds wrong at review; The same kind of correction is made repeatedly at a review gate; A phrase in later output cannot be explained

1. Before editing a stage output, ask whether this is a one-off human-judgment improvement or a kind of edit you have made before.
2. If it is a one-off improvement the system could not have produced, such as a turn of phrase, edit the output directly and move on.
3. If you keep making the same kind of edit, treat it as a diagnostic signal and trace it back to the source-level file that governs that stage.
4. Fix the source: amend the stage contract with an explicit constraint, or update the reference file, such as adding a stronger example of the target register to the voice guide.
5. Re-run the stage to confirm the recurring edit is no longer needed.

| Parameter | Value | Tested range | Source |
|---|---|---|---|
| Repeat threshold for treating an edit pattern as a source-level problem (proposed for a future ICM version, not an existing feature) | same kind of edit in the same stage's output 3 runs in a row | - | p. 18 |

Boundaries (where the source says this held; re-check before applying):
- Creative content is fuzzier than compiled code, and some output needs a human touch that cannot be reduced to a source-level rule. Editing the output is the right move there.
- Only recurring edits are diagnostic. One-off value-adding edits are not.
- Automatic tracking of output edits across runs is described as a possible future version, not a current capability. Until then, the practitioner has to notice the patterns manually.
- Tracing a problem back to its source relies on the debugging and traceability infrastructure described in the previous subsection.
- This is an argument drawn from software engineering practice, not a tested result. Editing output at review gates is described as useful and working.
- Tracing is currently manual. The source says there is no direct way to link an output phrase to its causing instruction.
- The source proposes provenance markers, such as GUIDs, section tags or comment annotations, and markdown breakpoints as future tools. They are not implemented.

Pitfalls:
- Hand-editing the same output flaw every run, which leaves the source unchanged so the workspace stays only as good as the last human edit.
- Rewriting source rules to chase a one-off stylistic preference that was actually a legitimate human touch.
- Trying to fix a recurring problem without being able to trace it to a source file.
- Patching only the output fixes this run and leaves the cause, so the problem recurs in every future run.
- Blaming the wrong source after a manual trace leads to a fix that does not remove the problem.

Evidence behind this unit:
- Grade C (practitioner heuristic): Recurring output edits point to fixable source-level problems, for example a stage contract that should limit the opening or a voice guide that needs a stronger register example. This is argued by the authors, with no measured results. (p. 18). Conditions: Authors' design reasoning for ICM workspaces; no data or experiment reported in this section.
- Grade C (practitioner heuristic): Editing the output fixes this run, while editing the source fixes every future run. The source frames output editing as patching the binary. (p. 17). Conditions: Conceptual argument by analogy to compilers. No empirical data are given.
Inference (not stated in the source): The step-by-step order (classify the edit, trace it to a source file, fix it, re-run) is an operationalization of the authors' principle, not stated as a numbered procedure in the source.
Inference (not stated in the source): Using 3 repeats as a manual rule of thumb borrows the number from the proposed automated tracking feature.
Inference (not stated in the source): The step of re-running the stage after the source fix is implied by the incremental re-run practice. It is not stated in this passage.

### Check whether ICM's evidence covers your model and use case before relying on its claims
<!-- unit:u21 -->
When: Considering ICM for a model other than Claude Opus 4.6 or Sonnet 4.6; Expecting proven quality gains over monolithic prompting; Planning to use ICM for academic or policy work

1. Confirm which model family you will use. The source tested only Claude Opus 4.6 and Sonnet 4.6.
2. If using another model, treat equivalence as an open empirical question and pilot it on your own workspace before committing.
3. Do not assume scoped context beats monolithic prompting on your task. Run your own comparison on the same task if the difference matters.
4. For academic or policy use, treat the deployments as early-stage.

Boundaries (where the source says this held; re-check before applying):
- Do not apply as proven when using non-Claude models. The protocol is model-agnostic by design (folder structure, file formats, naming), but equivalent results are untested.
- Do not claim a measured quality gain from staged context. The claim rests on 'lost in the middle' literature and practitioner judgment, with no controlled comparison against monolithic prompting.
- Most active use is content production; academic and policy outcomes cannot yet be reported in detail.
- Evidence base is informal conversations with a self-selected, invite-only community (selection and enthusiasm bias).

Pitfalls:
- Assuming vendor-portability means output-quality portability.
- Quoting the 30 of 33 U-shape figure as verified.

Evidence behind this unit:
- Grade C (practitioner heuristic): No controlled comparison of staged context loading versus monolithic prompting has been conducted, so the quality claim rests on theory and practitioner judgment. (p. 13). Conditions: Authors' own statement of limitations.
- Grade C (practitioner heuristic): All testing used a single model family (Claude Opus 4.6 and Sonnet 4.6); whether other models give equivalent results is an empirical question. (p. 10). Conditions: Authors' statement; protocol itself imposes no vendor lock-in.

Time-sensitive: check current conditions before reusing these values.
Inference (not stated in the source): The advice to pilot or compare on your own task is an extrapolation; the source only says cross-model and controlled comparisons are future work.


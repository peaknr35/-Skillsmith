# Evidence: folder-structured-agent-workflows

Source: *Interpretable Context Methodology: Folder Structure as Agentic Architecture* by Jake Van Clief; David McDermott (file icm-2603.16021v2.pdf). Page cites such as (p. N) refer to that document. They are for checking this skill; cite them in an answer only when the user asks or a number is decisive, and then name the document in plain words.

Pages: `p. N` is the printed page of the source edition; `pdf p. N` is used when the printed page is unknown.
Grades: A = controlled result (experiment or proof); B = observational study, case study or un-ablated benchmark; C = practitioner heuristic or anecdote. Lines marked Inference are not stated in the source.
A page cite shows where a claim was found; it does not prove the claim supports the advice built on it. Run `skillsmith audit` for a support check.

## Check whether a workflow fits the folder-per-stage (ICM) design before adopting it
Built from stage-03 units: ch05-u01, ch07-u02, ch02-u01, ch01-u01, ch03-u09
- [C: practitioner heuristic] ICM has been applied to sequential, human-reviewed, repeatable workflows in content production, training material, academic research and policy analysis; its unsuitable cases are real-time multi-agent, high-concurrency and automated-branching systems. (p. 14 (locator: "ICM is local-first by design.")). Conditions: Authors' description of their own deployments and design boundaries; no controlled comparison reported in this section.
- [C: practitioner heuristic] The authors claim that for practitioners whose AI workflows are sequential, reviewable, and repeatable, ICM gives full pipeline capability with no framework to learn, no server to maintain, and no developer needed for day-to-day operation. (p. 18 (locator: "sequential, reviewable, and repeatable")). Conditions: The authors' concluding claim; this section reports no measurements. It holds for the stated workflow class only.
- [C: practitioner heuristic] For sequential, human-reviewed workflows, the folder approach simplifies six common operations, while frameworks provide error recovery, conditional branching, concurrency and richer service integration that the folder approach lacks or handles less well. (p. 2 (locator: "Manual re-run of failed stage")). Conditions: Author-built qualitative comparison table; no measurements; sequential, human-reviewed workflows.
- [C: practitioner heuristic] For sequential workflows, frameworks solve a coordination problem that may not need to exist, since the same coordination can be done with files in folders. (p. 3 (locator: "solve a coordination problem that may not need to exist")). Conditions: Authors' argument for sequential workflows only; they say frameworks work well for dynamic multi-agent collaboration, concurrency or complex branching.
- [C: practitioner heuristic] Frameworks suit complex, concurrent systems but add engineering overhead for sequential, human-reviewed workflows; for these the control surface can be much simpler. (p. 1 (locator: "sequential workflows where a human reviews output at each step")). Conditions: Authors' framing in the abstract and introduction; no data or experiment is presented in this section.
- [C: practitioner heuristic] ICM trades the flexibility of a programmatic orchestrator for the portability, inspectability and editability of plain files. (p. 8 (locator: "That tradeoff is the point.")). Conditions: Authors' stated design tradeoff, supported by an appeal to Gabriel and Plan 9; not tested.
- Inference (not in the source): Workflows that are non-sequential, not human-reviewable, or one-off are inferred to be a poor fit. The source states only the fit condition, not the converse.
- Inference (not in the source): The newsletter scenario and the hybrid suggestion are illustrative applications, not stated in the source.
- Inference (not in the source): Advice to prefer file edits when the workflow changes often is inferred from the authors' complaint about editing code; it is not stated as a rule.
- Inference (not in the source): What kinds of workflows (branching, parallel) exceed the folder approach is inferred from the stated flexibility tradeoff; the source does not enumerate them.

## Organize an agent workspace as numbered stage folders with a five-layer context hierarchy
Built from stage-03 units: ch03-u01, ch01-u02
- [C: practitioner heuristic] The five-layer hierarchy with approximate token sizes per layer; no agent reads everything, which keeps token cost low and context focused. (p. 6 (locator: "No agent reads everything.")). Conditions: Authors' architecture description; no controlled comparison in this section.
- [C: practitioner heuristic] If each stage's prompts and context already exist as files in a well-organized folder hierarchy, a coordination framework is not needed; one agent reading the right files at the right moment suffices. (p. 1 (locator: "one orchestrating agent that reads the right files")). Conditions: Stated as the authors' central observation; no empirical test is reported in this section.
- Default Layer 0 (CLAUDE.md) size = ~800 tokens (p. 5)
- Default Layer 1 (workspace CONTEXT.md) size = ~300 tokens (p. 5)
- Default Layer 2 (stage CONTEXT.md) size = 200-500 tokens (p. 5)
- Default Layer 3 (reference material) size = 500-2k tokens (p. 5)
- Inference (not in the source): Applying the layout to non-video workflows such as newsletters is an extrapolation; the source's example is a script-to-animation workspace.
- Inference (not in the source): The example folder names and the sample workflow are illustrative, not from the source.
- Inference (not in the source): The 'edit files to change workflow' step is inferred from the authors' contrast with editing code.

## Write each stage as a contract with Inputs, Process and Outputs
Built from stage-03 units: ch03-u03
- [C: practitioner heuristic] The Inputs table makes context selection explicit, editable and auditable, and makes Layer 2 the control point of the system. (p. 7 (locator: "Layer 2 is the control point of the entire system.")). Conditions: Authors' design argument; no measurements in this section.
- [C: practitioner heuristic] Typical contract has three parts (inputs, process, outputs), and the instruction files double as documentation so a new team member can read them top to bottom. (p. 9 (locator: "A typical stage contract looks like this:")). Conditions: Illustrated with one example script-stage contract.

## Separate reference material (Layer 3) from working artifacts (Layer 4)
Built from stage-03 units: ch03-u02, ch05-u03
- [C: practitioner heuristic] Layer 3 is stable, internalized as constraints, and lives in references/, _config/, shared/. Layer 4 changes every run, is processed as input, and lives in output/. (p. 6 (locator: "Layer 3 is reference material")). Conditions: Design rationale from the authors; no experiment reported in this section.
- [C: practitioner heuristic] Stages where reference and working material are clearly separated produced more consistent adherence to style and format guidelines. (p. 15 (locator: "early practitioner experience suggests")). Conditions: Early practitioner experience, not a controlled comparison; flat-context benefit untested.

## Give each stage exactly one job and a readable input and output
Built from stage-03 units: ch03-u05, ch02-u04
- [C: practitioner heuristic] Each stage handles a single workflow step and writes to its own folder, reading a defined input and writing a defined output. (p. 5 (locator: "One stage, one job.")). Conditions: Design principle justified by analogy to established software practice.
- [C: practitioner heuristic] Unix design principles: do one thing well, make every output usable as another's input, and use text streams as the universal interface. (p. 2 (locator: "make each program do one thing well")). Conditions: Historical design principles from McIlroy (1978); not an empirical test on AI workflows.
- [C: practitioner heuristic] In the pipe-and-filter pattern any component can be replaced, inspected or tested independently. (p. 3 (locator: "replaced, inspected, or tested independently")). Conditions: Architectural claim of Shaw and Garlan as cited; no measurements.
- Inference (not in the source): Mapping each principle to specific file-naming conventions is not in the source.

## Use plain text files as the interface between stages
Built from stage-03 units: ch03-u06
- [C: practitioner heuristic] Any tool that reads a text file can participate in the workflow, and any human with a text editor can inspect or modify any artifact. (p. 5 (locator: "Plain text as the interface.")). Conditions: Argument from Kernighan and Pike's text-as-universal-interface; no measurements.
- Inference (not in the source): Large binary assets (images, video) are not covered by the source; handling them alongside text handoffs is not specified.

## Insert a human review gate at every stage boundary
Built from stage-03 units: ch04-u01, ch03-u04
- [C: practitioner heuristic] In the script-to-animation workspace, the human reviews and edits the output at each stage boundary, and the next stage works with whatever the human left. (p. 11 (locator: "At each stage boundary, the human reviews the output.")). Conditions: Author-built workspace, single Claude Code session, Claude Opus 4.6 and Sonnet 4.6; descriptive account, not a controlled test.
- [C: practitioner heuristic] Each stage boundary lets the human inspect and edit the output before the next stage runs, and the next stage picks up the edited file. (p. 8 (locator: "the human can inspect and edit the output before the next stage runs")). Conditions: Design description (mixed-initiative and direct-manipulation framing); no user study in this section.
- Inference (not in the source): Applying the gate pattern to non-media workflows such as newsletters is an extrapolation from the script-to-animation example.

## Scope each stage's context tightly and check it against the token budget
Built from stage-03 units: ch03-u08, ch02-u02, ch05-u02
- [C: practitioner heuristic] Representative token counts from one script-to-animation workspace: each of three ICM stages delivers 2,000-8,000 focused tokens, versus a monolithic prompt of about ~42k tokens in the figure (the text says such a prompt can easily reach 30,000 to 50,000). (p. 8 (locator: "That approach can easily reach 30,000 to 50,000 tokens")). Conditions: Representative token counts from one script-to-animation workspace; no model-accuracy comparison reported here.
- [B: observational or case study] LLMs perform significantly worse when relevant information is buried in the middle of long contexts, and more irrelevant material in the window means worse performance on the material that matters. (p. 4 (locator: "buried in the middle of long contexts")). Conditions: Finding from Liu et al., cited secondhand in this paper; no numbers given; long contexts.
- [C: practitioner heuristic] Stages with tightly scoped context (clear instructions, limited reference material, specific output format) produced more consistent results than stages with broad context. (p. 15 (locator: "tightly scoped context")). Conditions: Early practitioner pattern in ICM use on one model family; no controlled comparison.
- Default Layers 0-2 combined = roughly 1,300 to 1,600 tokens (p. 7)
- Default Layer 3 per stage = typically 500 to 2,000 tokens (p. 7)
- Default Total context per stage = typically 2,000 to 8,000 tokens (p. 7)
- Default prompt compression token reduction reported by Jiang et al. (alternative to avoidance) = up to 20x with minimal performance loss (p. 4)
- Default typical ICM context size per stage = 2,000 to 8,000 tokens (p. 15)
- Inference (not in the source): The statement that these sizes are 'well within the range where current models perform at their best' depends on current models; check against the model you use.
- Inference (not in the source): The advice to reference only the needed files from the stage instructions is an implementation detail not stated in the source.
- Inference (not in the source): Narrowing context before changing the model is a practical inference from the stated pattern, not a claim in the source.

## Audit each stage's context using write, select, compress and isolate
Built from stage-03 units: ch02-u05
- [C: practitioner heuristic] Context engineering strategies can be organized as write, select, compress and isolate. (p. 3 (locator: "write (author instructions), select (choose relevant context)")). Conditions: Practitioner taxonomy from LangChain as cited; not experimentally validated here.

## Scope tool definitions per stage and layer MCP inside stages
Built from stage-03 units: ch02-u03
- [C: practitioner heuristic] Loading all tool definitions upfront slows agents and increases costs; stage-scoped tool definitions avoid this. (p. 4 (locator: "loading all tool definitions upfront into the context window")). Conditions: Observation attributed to Jones and Kelly at Anthropic; no numbers; the avoidance benefit is the authors' argument.

## Configure the factory once, then run the pipeline for each product
Built from stage-03 units: ch03-u07
- [C: practitioner heuristic] Workspace is configured once; each run produces a new deliverable with the same configuration, following continuous-delivery repeatability. (p. 5 (locator: "Configure the factory, not the product.")). Conditions: Design principle; no repeatability data in this section.

## Check that a pipeline gives humans visible state and review points
Built from stage-03 units: ch02-u06
- [B: observational or case study] Opaque automated outputs lead to misuse or disuse, both because the human cannot see what happened between input and output. (p. 4 (locator: "the human cannot see what happened between input and output")). Conditions: Parasuraman and Riley, cited secondhand; qualitative; automation in general, not specifically LLM workflows.
- [B: observational or case study] Systems should let users invoke, adjust and terminate automated processes at natural breakpoints, which requires visible state and reversible actions. (p. 4 (locator: "invoke, adjust, and terminate automated processes at natural breakpoints")). Conditions: Horvitz mixed-initiative principles, cited secondhand; qualitative.
- Inference (not in the source): The sign-off step in the example is an illustrative application; the source does not prescribe it.
- Inference (not in the source): Regulatory suitability of any specific pipeline is not established by the source.

## Allocate review effort in a staged pipeline using the U-shaped editing pattern
Built from stage-03 units: ch04-u02
- [C: practitioner heuristic] 30 of 33 practitioners reported heavy editing at stage 1, light editing in the middle stages, and heavy editing again at the final stage; 3 reported roughly equal editing across stages. (p. 12 (locator: "30 report an intervention pattern consistent with a U-shape")). Conditions: Self-report through conversations with an invite-only community; script-to-animation or structurally similar multi-stage workspaces; not instrumented.
- Inference (not in the source): The advice to skim middle stages only when both anchors exist is the source's explanation of why practitioners trust them, restated as a condition.

## Surface the structural plan as an editable file before drafting (course deck workflow)
Built from stage-03 units: ch04-u03
- [C: practitioner heuristic] Exposing the structural plan as an editable file lets the human correct it at the cheapest point, before slides are drafted. (p. 11 (locator: "course-correct at the point where correction is cheapest")). Conditions: Qualitative description of the author's course deck workspace; no measurements.

## Decide whether to build a new workspace with the builder or duplicate an existing one
Built from stage-03 units: ch04-u04
- [C: practitioner heuristic] In practice people often prefer to copy and adapt an existing workspace rather than start from a blank one. (p. 13 (locator: "people often prefer to copy and adapt an existing one")). Conditions: Informal community observations from an invite-only group; limited set of workflow types.
- [C: practitioner heuristic] The workspace-builder is a five-stage workspace (discovery, stage mapping, scaffolding, questionnaire design, validation) whose output is a new workspace. (p. 11 (locator: "a five-stage workspace whose output is a new workspace")). Conditions: Descriptive account of the tool by its authors.

## Tune stage behavior by editing CONTEXT.md in plain text
Built from stage-03 units: ch04-u05
- [C: practitioner heuristic] Non-technical users successfully modified stage behavior by editing markdown CONTEXT.md files (tone, constraints, emphasis). (p. 13 (locator: "successfully modified stage behavior by editing the markdown")). Conditions: Informal practitioner reports from an invite-only community of 52 members; no formal data collection.
- Default example length constraint = keep scripts under 90 seconds (p. 13)
- Inference (not in the source): The example uses tone and length constraints, which the source names only as categories of edits.

## Audit and correct a pipeline run by reading the stage files
Built from stage-03 units: ch05-u04
- [C: practitioner heuristic] Because every intermediate output is a plain file, the system is observable by default; stage contracts, editable markdown and review gates map to Amershi et al.'s guidelines on clarity, correction and dismissal. (p. 14 (locator: "You open a folder and read the files.")). Conditions: Authors' architectural argument; no user study reported in this section.

## Re-run only the stale stages instead of the whole pipeline
Built from stage-03 units: ch06-u01
- [C: practitioner heuristic] ICM supports incremental re-running: a practitioner re-runs stage 2 without touching stage 1, and a changed voice guide triggers only the stages that load it. (p. 16 (locator: "re-runs stage 2 without touching stage 1")). Conditions: Practitioner description of the ICM script-to-animation workspace. The compiler analogy is the authors' framing and no controlled test is reported.
- Inference (not in the source): The step of also treating downstream stages as possibly stale follows from the pipeline structure. The source does not state it explicitly.

## Add a cross-stage audit that re-checks stage n output against stage n-2
Built from stage-03 units: ch06-u02
- [C: practitioner heuristic] The authors report that an audit file forcing the agent to trace the specification back to the original script and re-verify timing per phrase catches most alignment errors. The authors call it a proto-debugger. (p. 17 (locator: "an audit file that forces the agent to trace back")). Conditions: Practitioner observation in the script-to-animation workspace. No quantitative rate is given.
- Inference (not in the source): Applying the audit to non-animation workspaces such as slide decks is an extrapolation from the source's single example workspace.

## Decide whether to edit an output or fix its source, and treat recurring edits as debugging signals
Built from stage-03 units: ch07-u01, ch06-u03
- [C: practitioner heuristic] Recurring output edits point to fixable source-level problems, for example a stage contract that should limit the opening or a voice guide that needs a stronger register example. This is argued by the authors, with no measured results. (p. 18 (locator: "These recurring edits are debugging information.")). Conditions: Authors' design reasoning for ICM workspaces; no data or experiment reported in this section.
- [C: practitioner heuristic] Editing the output fixes this run, while editing the source fixes every future run. The source frames output editing as patching the binary. (p. 17 (locator: "Editing the output fixes this run")). Conditions: Conceptual argument by analogy to compilers. No empirical data are given.
- Default Repeat threshold for treating an edit pattern as a source-level problem (proposed for a future ICM version, not an existing feature) = same kind of edit in the same stage's output 3 runs in a row (p. 18)
- Inference (not in the source): The step-by-step order (classify the edit, trace it to a source file, fix it, re-run) is an operationalization of the authors' principle, not stated as a numbered procedure in the source.
- Inference (not in the source): Using 3 repeats as a manual rule of thumb borrows the number from the proposed automated tracking feature.
- Inference (not in the source): The step of re-running the stage after the source fix is implied by the incremental re-run practice. It is not stated in this passage.

## Check whether ICM's evidence covers your model and use case before relying on its claims
Built from stage-03 units: ch04-u06
- [C: practitioner heuristic] No controlled comparison of staged context loading versus monolithic prompting has been conducted, so the quality claim rests on theory and practitioner judgment. (p. 13 (locator: "No controlled comparison has been conducted")). Conditions: Authors' own statement of limitations.
- [C: practitioner heuristic] All testing used a single model family (Claude Opus 4.6 and Sonnet 4.6); whether other models give equivalent results is an empirical question. (p. 10 (locator: "Whether the results would be equivalent is an empirical question")). Conditions: Authors' statement; protocol itself imposes no vendor lock-in.
- Inference (not in the source): The advice to pilot or compare on your own task is an extrapolation; the source only says cross-model and controlled comparisons are future work.

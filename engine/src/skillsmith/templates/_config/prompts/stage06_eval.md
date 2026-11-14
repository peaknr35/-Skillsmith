You are running stage 06_eval for the skill below.

Skill name: {{NAME}}
Description: {{DESCRIPTION}}
Action units: {{UNIT_TITLES}}

Write:
- >=10 should_fire prompts: varied realistic user phrasings that must trigger this skill.
- >=10 should_not_fire prompts: NEARBY requests that look similar but must not trigger it (use the description's exclusions).
- 3 to 5 tasks that test whether the skill CHANGES THE MODEL'S DESIGN CHOICES, not whether the model can follow instructions.

Neutral-task rule (a prompt that names the method does the skill's routing work and invalidates the comparison):
- cue_words: 5 to 12 signature terms of the method, words a user would only use if they already knew it: its own name, its file names, its named layers, patterns and artifacts. Copy each one EXACTLY as it is written in the skill text below (a cue word that is not literally in that text is rejected). Do NOT use everyday words as cue words (workflow, pipeline, process, step, agent, AI, context, model, review, output): neutral tasks must still be allowed to use them.
- At least 2 tasks MUST be neutral (neutral = true): they describe only the operational problem, constraints and requirements in everyday words, and contain NONE of the cue words. Do not mention the paper, the method name, or any architectural hint.
  Bad neutral task: "Design a weekly report workflow using the folder-based approach."
  Good neutral task: "I need to automate a weekly report compiled from 20 sources. A human editor must review and adjust the selection and tone before publication. How should I architect and run this AI system?"
- Neutrality is checked by code, not by your label: a task counts as neutral only if its prompt contains none of your distinctive cue words. At least 2 tasks must qualify, so write them as everyday problem statements.
- Other tasks (neutral = false) may name the method but must test applying its details (defaults, boundaries, order).
- At least 1 task should be a near-miss applicability check (`expect_apply`: false) when you write 4 or 5 tasks: a realistic problem in a neighbouring area where a boundary in the skill's `When NOT to apply` or `Fit check` is violated (for example real-time multi-agent chat or high-concurrency serving for a sequential file-based method). A good answer with the skill loaded solves the user's problem in their own terms and explains briefly why this method is not the right fit, WITHOUT imposing the method's vocabulary. For tasks where the method fits, set `expect_apply`: true.
- For every task give: baseline_expectation (what a model WITHOUT the skill will most likely propose) and treatment_expectation (what the skill should make it propose instead); baseline_markers (3 to 6 strings a generic answer is likely to contain, e.g. library or tool names); treatment_markers (3 to 6 strings that should appear when the skill is applied; each must appear in the skill text below).
- expected_differences: specific, checkable behaviours with the skill (fit check first, defaults as starting points, boundary checks). Do not invent numbers.
- process_checks: 2 to 4 pass/fail checks on HOW the answer proceeds (SkillForgeBench, arXiv 2610.14918: process rubrics vs completion rubrics; strict completion requires every item to pass at once). Phrase them in the user's terms: for example "Checks whether the user's constraints fit before prescribing an architecture", "Does not use internal unit ids or unexplained jargon", "Addresses every constraint in the prompt".
- config_file_to_edit_on_failure: the _config/ file to edit if the skill fails these tests (for example _config/skill-template.md).

Skill text (SKILL.md followed by playbook.md; cue words and treatment markers must be found here):
{{SKILL_TEXT}}

Return ONLY JSON matching this schema:
{{SCHEMA}}

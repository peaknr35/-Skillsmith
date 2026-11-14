"""Pydantic models: the contract every stage output is validated against."""
from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FIRST_SECOND_PERSON = re.compile(
    r"\b(?:i(?![/'\w])|i'(?:m|ll|ve|d)|me|my|myself|we|our|ours|ourselves|you|your|yours|yourself)\b", re.I)


# quoted example user phrasings ("do I need X?", 'set up my workflow') are allowed to be first person
QUOTED = re.compile(r"\"[^\"]+\"|“[^”]+”|(?<![\w])'[^']{3,}?'(?![\w])")


def check_description(v: str) -> str:
    """Trigger-first, third person: 'Use when <situations, tasks, phrasings>. ...'"""
    if len(v) > 1024 or len(v) < 20:
        raise ValueError("description must be 20-1024 chars")
    if not v.startswith("Use when "):
        raise ValueError("description must start with 'Use when ' followed by the triggering situations")
    if FIRST_SECOND_PERSON.search(QUOTED.sub(" ", v)):  # quoted user phrasings may use I/my
        raise ValueError("description must be third person outside quoted example phrasings (no I/we/you)")
    return v


class Grade(str, Enum):
    A = "A"  # controlled / replicated
    B = "B"  # observational / ablation
    C = "C"  # practitioner heuristic / anecdote


class SourceType(str, Enum):
    method = "method"
    empirical = "empirical"
    framework = "framework"
    survey = "survey"
    position = "position"


class Citation(BaseModel):
    """Dual-page citation. pdf_page is always known; printed_page is None when the
    printed-page offset could not be established (never guessed)."""
    pdf_page: int = Field(ge=1)
    printed_page: int | None = Field(default=None, ge=1)
    quote_hint: str | None = None  # short locator, checked against the section text


class Default(BaseModel):
    parameter: str
    value: str
    tested_range: str | None = None
    cite: Citation  # required: a default without a page cite is rejected


class Evidence(BaseModel):
    claim: str
    grade: Grade
    conditions: str
    cite: Citation  # required


class ActionUnit(BaseModel):
    id: str = ""
    title: str = Field(min_length=3)
    triggers: list[str] = Field(min_length=1)
    procedure: list[str] = Field(min_length=1)
    defaults: list[Default] = []
    boundaries: list[str] = Field(min_length=1)
    failure_modes: list[str] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    example: str = Field(min_length=3)
    time_sensitive: bool = False
    extrapolations: list[str] = []
    script_candidate: bool = False
    source_units: list[str] = []  # stage-03 unit ids this unit was built from (set at consolidation)

    def cites(self) -> list[Citation]:
        return [d.cite for d in self.defaults] + [e.cite for e in self.evidence]

    def corpus(self) -> str:
        """Text a number in generated output may legitimately come from.

        The worked example is excluded on purpose: it is illustrative, not sourced.
        """
        parts = [self.title, *self.triggers, *self.procedure, *self.boundaries,
                 *self.failure_modes, *self.extrapolations]
        for d in self.defaults:
            parts += [d.parameter, d.value, d.tested_range or ""]
        for e in self.evidence:
            parts += [e.claim, e.conditions]
        return "\n".join(parts)


# What a source can honestly become (survey 2608.29596; SkillAlchemy 2608.23417 "admission"):
# execution_skill  = steps an agent follows to change state (the full skill template)
# decision_guide   = criteria for choosing between options; no fixed step order
# evidence_reference = graded claims and their conditions; prescribes nothing
# Sources with none of these abstain at the map (actionable=false).
ArtifactType = Literal["execution_skill", "decision_guide", "evidence_reference"]
ARTIFACT_TYPES = ("execution_skill", "decision_guide", "evidence_reference")


class Triad(BaseModel):
    """Membership test for an execution skill (A Systematic Survey of Agentic Skills, arXiv 2608.29596).
    All three must hold for artifact=execution_skill; otherwise choose a weaker artifact or abstain."""
    modular: bool  # can be packaged and versioned outside model weights and harness code
    late_binding: bool  # an activation condition can decide, per request, whether to load it
    state_transforming: bool  # tells the agent how to act / change state, not only what is true
    note: str = ""


class SkillProposal(BaseModel):
    name: str
    description: str
    role: Literal["router", "standard"] = "standard"
    artifact: ArtifactType = "execution_skill"
    section_ids: list[str] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not KEBAB.match(v) or len(v) > 64:
            raise ValueError("name must be kebab-case, <=64 chars")
        return v

    @field_validator("description")
    @classmethod
    def _desc(cls, v: str) -> str:
        return check_description(v)


class ChapterTriage(BaseModel):
    id: str
    pages: str
    triage: Literal["procedure", "framework", "evidence", "skip"]
    self_summary: bool = False  # the book's own review/summary chapter
    note: str = ""


class SourceMap(BaseModel):
    source_type: SourceType
    actionable: bool
    gate_reason: str = Field(min_length=3)
    chapters: list[ChapterTriage]
    triad: Triad | None = None  # required when any proposal is an execution_skill (checked below)
    proposed_skills: list[SkillProposal] = []

    @model_validator(mode="after")
    def _need_skills(self) -> "SourceMap":
        if self.actionable and not self.proposed_skills:
            raise ValueError("actionable source must propose at least one skill")
        if self.actionable and any(p.artifact == "execution_skill" for p in self.proposed_skills):
            # A missing triad is tolerated here so maps approved before this field existed still load;
            # stage 02 requires it for every new map (runner.stage_map).
            t = self.triad
            if t is not None and not (t.modular and t.late_binding and t.state_transforming):
                raise ValueError("the triad test failed, so no proposal may be an execution_skill: use "
                                 "decision_guide or evidence_reference, or set actionable=false")
        return self


class SkillSpec(BaseModel):
    name: str
    description: str
    role: Literal["router", "standard"] = "standard"
    artifact: ArtifactType = "execution_skill"  # set from the approved map at stage 05
    units: list[ActionUnit] = Field(min_length=1)
    excluded: list[str] = []

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not KEBAB.match(v) or len(v) > 64:
            raise ValueError("name must be kebab-case, <=64 chars")
        return v

    @field_validator("description")
    @classmethod
    def _desc(cls, v: str) -> str:
        return check_description(v)


class ConsolidationResult(BaseModel):
    skills: list[SkillSpec] = Field(min_length=1)
    conflicts: list[str] = []
    ethics_log: list[str] = []


class EvalTask(BaseModel):
    prompt: str
    expected_differences: list[str] = Field(min_length=1)
    neutral: bool = False  # states only the problem; contains none of the method's signature vocabulary
    baseline_expectation: str = ""  # what a model without the skill is expected to propose
    treatment_expectation: str = ""  # what a model with the skill is expected to propose
    treatment_markers: list[str] = []  # strings that should appear with the skill (must occur in the skill text)
    baseline_markers: list[str] = []  # strings a generic answer would likely contain instead
    # False = a nearby problem the method does NOT fit: a good answer solves it without imposing the method
    # (the over-application failure measured on the ICM run; Procedural Exposure Bias, arXiv 2610.26062).
    expect_apply: bool = True
    # requirement-level checks phrased in the user's terms, each pass/fail; "strict" = all pass
    # (completion + process rubrics, SkillForgeBench arXiv 2610.14918)
    process_checks: list[str] = []


class EvalSet(BaseModel):
    skill: str
    should_fire: list[str] = Field(min_length=10)
    should_not_fire: list[str] = Field(min_length=10)
    tasks: list[EvalTask] = Field(min_length=3, max_length=5)
    # signature vocabulary of the method: words a user would only use if they already knew it.
    # Each must occur in the skill text; neutral task prompts must contain none of them.
    cue_words: list[str] = []
    config_file_to_edit_on_failure: str = "_config/skill-template.md"


class CompiledSkill(BaseModel):
    spec: SkillSpec
    skill_md: str
    tool_schema: dict
    system_prompt: str
    playbook_md: str
    evidence_md: str
    mode: str = "full"  # how SKILL.md was rendered: full | lean | index

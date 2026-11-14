"""Plan-based consolidation. The model returns a small MERGE PLAN (which units to keep,
which to fold into which, which to exclude and why); code builds the merged units from the
original units. Citations, numbers and defaults are inherited, never re-typed by the model,
so they cannot be altered or invented at this stage, and the reply stays small."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .accounting import excluded_ids
from .schema import ActionUnit, ConsolidationResult, SkillProposal, SkillSpec


class PlanError(ValueError):
    """The merge plan is inconsistent with the input units (triggers a retry with the reason)."""


class PlanUnit(BaseModel):
    primary: str = Field(description="id of the input unit that is the most specific version")
    also: list[str] = Field(default=[], description="ids of input units folded into the primary one")
    title: str | None = Field(default=None, description="optional clearer verb-first title; no new numbers")


class PlanSkill(BaseModel):
    name: str
    description: str | None = None
    units: list[PlanUnit] = Field(min_length=1)
    excluded: list[str] = Field(default=[], description="'unit-id: reason' for every input unit not carried")


class ConsolidationPlan(BaseModel):
    skills: list[PlanSkill] = Field(min_length=1)
    conflicts: list[str] = []
    ethics_log: list[str] = []


def _uniq(items):
    seen, out = set(), []
    for i in items:
        key = i if isinstance(i, str) else repr(i)
        if key not in seen:
            seen.add(key)
            out.append(i)
    return out


def merge_units(primary: ActionUnit, others: list[ActionUnit], title: str | None) -> ActionUnit:
    """Primary unit's procedure and example; everything else is the order-preserving union."""
    group = [primary, *others]
    u = primary.model_copy(deep=True)
    u.title = title or primary.title
    u.triggers = _uniq(t for g in group for t in g.triggers)
    u.boundaries = _uniq(b for g in group for b in g.boundaries)
    u.failure_modes = _uniq(f for g in group for f in g.failure_modes)
    u.extrapolations = _uniq(x for g in group for x in g.extrapolations)
    seen_d, defaults = set(), []
    for g in group:
        for d in g.defaults:
            k = (d.parameter.lower(), d.value)
            if k not in seen_d:
                seen_d.add(k)
                defaults.append(d)
    u.defaults = defaults
    seen_e, evidence = set(), []
    for g in group:
        for e in g.evidence:
            ek = (e.claim.lower(), e.cite.pdf_page)
            if ek not in seen_e:
                seen_e.add(ek)
                evidence.append(e)
    u.evidence = evidence
    u.time_sensitive = any(g.time_sensitive for g in group)
    u.script_candidate = any(g.script_candidate for g in group)
    u.source_units = _uniq(i for g in group for i in (g.source_units or [g.id]))
    return u


def apply_plan(plan_skill: PlanSkill, prop: SkillProposal, by_id: dict[str, ActionUnit]) -> SkillSpec:
    """Validate the plan against the input ids, then build the SkillSpec. Raises PlanError."""
    used: list[str] = []
    for pu in plan_skill.units:
        used += [pu.primary, *pu.also]
    unknown = sorted({i for i in used if i not in by_id})
    if unknown:
        raise PlanError(f"plan names unit ids that are not in the input: {unknown}")
    excl = excluded_ids(plan_skill.excluded, set(by_id))
    carried = set(used)
    missing = sorted(set(by_id) - carried - excl)
    if missing:
        raise PlanError(
            f"unit accounting failed: input units neither carried (as `primary` or in `also`) nor listed in "
            f"`excluded` as 'unit-id: reason': {missing}. Never drop a unit silently.")
    dup = sorted({i for i in used if used.count(i) > 1})
    if dup:
        raise PlanError(f"each input unit may be carried once; used more than once: {dup}")
    both = sorted(carried & excl)
    if both:
        raise PlanError(f"units both carried and excluded: {both}")
    units = [merge_units(by_id[pu.primary], [by_id[i] for i in pu.also], pu.title) for pu in plan_skill.units]
    return SkillSpec(name=prop.name, description=plan_skill.description or prop.description,
                     role=prop.role, units=units, excluded=list(plan_skill.excluded))


def to_result(plan: ConsolidationPlan, prop: SkillProposal, by_id: dict[str, ActionUnit]) -> ConsolidationResult:
    if [s.name for s in plan.skills] != [prop.name]:
        raise PlanError(f"return exactly one skill named {prop.name!r}; got {[s.name for s in plan.skills]}")
    spec = apply_plan(plan.skills[0], prop, by_id)
    return ConsolidationResult(skills=[spec], conflicts=plan.conflicts, ethics_log=plan.ethics_log)

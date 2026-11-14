"""Review gates: only a human (via `approve`) creates APPROVED; the runner never does."""
from __future__ import annotations

from datetime import datetime, timezone

from .workspace import GATES, Workspace


class GateError(Exception):
    pass


def is_gate(stage: str) -> bool:
    return stage in GATES


def approve(w: Workspace, stage: str) -> None:
    if stage not in GATES:
        raise GateError(f"{stage} is not a review gate (gates: {sorted(GATES)})")
    if not w.done(stage):
        raise GateError(f"{stage} has no output to approve; run it first")
    (w.output(stage) / "APPROVED").write_text(
        f"approved {datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8")


def require_prereqs(w: Workspace, stage: str, stages: list[str]) -> None:
    for prev in stages[: stages.index(stage)]:
        if not w.done(prev):
            raise GateError(f"{prev} is not done; run it before {stage}")
        if prev in GATES and not w.approved(prev):
            raise GateError(
                f"{prev} is a review gate: review {w.output(prev)} then run "
                f"`skillsmith approve <workspace> {prev}`")

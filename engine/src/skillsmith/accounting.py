"""Unit accounting for consolidation: every input unit id is carried into an output unit's
`source_units` or listed in `excluded` with a reason. Ids, not counts (merging is legitimate)."""
from __future__ import annotations

import re


def excluded_ids(excluded: list[str], known: set[str]) -> set[str]:
    """Ids named before the first ':' of each 'unit-id[, unit-id]: reason' entry."""
    out: set[str] = set()
    for entry in excluded:
        head = entry.split(":", 1)[0]
        for tok in re.split(r"[,;\s]+", head):
            if tok in known:
                out.add(tok)
    return out


def account(input_ids: set[str], units, excluded: list[str]) -> tuple[set[str], set[str]]:
    """Return (missing, unknown): input ids neither carried nor excluded, and cited ids not in the input."""
    carried: set[str] = set()
    for u in units:
        carried.update(u.source_units)
    covered = carried | excluded_ids(excluded, input_ids)
    return input_ids - covered, carried - input_ids


def expand_merge_ids(unit_source_ids: list[str], merge_map: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for m in unit_source_ids:
        for o in merge_map.get(m, [m]):
            if o not in out:
                out.append(o)
    return out


def expand_excluded(excluded: list[str], merge_map: dict[str, list[str]]) -> list[str]:
    """Rewrite entries naming merge ids so they name the original stage-03 ids."""
    out = []
    for entry in excluded:
        head, sep, reason = entry.partition(":")
        toks = [t for t in re.split(r"[,;\s]+", head) if t]
        if any(t in merge_map for t in toks):
            ids = expand_merge_ids(toks, merge_map)
            out.append(f"{', '.join(ids)}:{reason}")
        else:
            out.append(entry)
    return out

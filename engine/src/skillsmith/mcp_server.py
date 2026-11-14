"""MCP server: serves exported skill folders to Claude (or any MCP client) over stdio.

Behaviour contract: a skill tool SELECTS playbook content for the caller's situation
(deterministic trigger/title overlap) and returns it with the boundaries to check.
It does not execute the playbook and does not call an LLM. With no match it says so."""

import json
import re
from pathlib import Path
from typing import Annotated, Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

STOP = {"the", "and", "for", "with", "that", "this", "when", "from", "into", "your", "have", "what",
        "how", "are", "can", "does", "was", "not", "but", "use", "using", "about", "need", "want"}


def _load(skills_dir: Path) -> dict[str, Path]:
    out = {}
    root = Path(skills_dir)
    for d in sorted(root.iterdir()) if root.is_dir() else []:
        if (d / "tool.json").is_file() and (d / "playbook.md").is_file():
            out[json.loads((d / "tool.json").read_text(encoding="utf-8"))["name"]] = d
    return out


def _unit_sections(playbook: str) -> dict[str, str]:
    out = {}
    for p in re.split(r"(?=^### )", playbook, flags=re.M):
        m = re.search(r"<!-- unit:(\S+) -->", p)
        if m:
            out[m.group(1)] = p.strip()
    return out


def _stem(w: str) -> str:
    for suf in ("ing", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _words(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3 and w not in STOP}


def select_units(playbook: str, situation: str, limit: int = 3) -> list[tuple[str, int, str]]:
    """Rank units by word overlap (light stemming) between the situation and each unit's
    title + 'When:' line. Only units scoring at least half of the best score are returned,
    which drops most single-generic-word noise. Still lexical, not semantic."""
    want = _words(situation)
    scored = []
    for uid, sec in _unit_sections(playbook).items():
        title = sec.splitlines()[0]
        when = next((ln for ln in sec.splitlines() if ln.startswith("When:")), "")
        score = len(want & _words(title + " " + when))
        if score:
            scored.append((uid, score, sec))
    scored.sort(key=lambda t: -t[1])
    # a single shared generic word is not a match once the situation has some substance
    min_score = 2 if len(want) >= 3 else 1
    scored = [t for t in scored if t[1] >= min_score]
    if not scored:
        return []
    best = scored[0][1]
    return [t for t in scored if t[1] * 2 >= best][:limit]


def build_server(skills_dir: Path) -> FastMCP:
    skills = _load(skills_dir)
    mcp = FastMCP("skillsmith")

    def list_skills() -> list[dict]:
        """List available skills with their trigger descriptions."""
        return [{"name": n, "description": json.loads((d / "tool.json").read_text(encoding="utf-8"))["description"]}
                for n, d in skills.items()]

    def get_playbook(name: str) -> str:
        """Return the full execution playbook for a skill."""
        if name not in skills:
            raise ValueError(f"unknown skill {name!r}; available: {sorted(skills)}")
        return (skills[name] / "playbook.md").read_text(encoding="utf-8")

    def get_system_prompt(name: str) -> str:
        """Return the system prompt fragment that teaches a model to use the skill."""
        if name not in skills:
            raise ValueError(f"unknown skill {name!r}; available: {sorted(skills)}")
        return (skills[name] / "system_prompt.md").read_text(encoding="utf-8")

    def match_skills(situation: str, limit: int = 3) -> list[dict]:
        """Selective skill exposure (SkillBrowser arXiv 2610.23554; SKALOS arXiv 2610.34728): compare a
        situation across all skills in the library by capability witnesses (matched units and their
        boundaries) so an agent loads only the skill and units whose capabilities fit."""
        out = []
        for n, d in skills.items():
            pb = (d / "playbook.md").read_text(encoding="utf-8")
            hits = select_units(pb, situation, limit=limit)
            if hits:
                tool = json.loads((d / "tool.json").read_text(encoding="utf-8"))
                out.append({"skill": n, "description": tool["description"],
                            "best_score": hits[0][1],
                            "matched_units": [{"unit_id": uid, "score": sc,
                                               "title": sec.splitlines()[0].lstrip("# ").strip()}
                                              for uid, sc, sec in hits]})
        out.sort(key=lambda r: -r["best_score"])
        return out[:limit]

    mcp.add_tool(list_skills)
    mcp.add_tool(get_playbook)
    mcp.add_tool(get_system_prompt)
    mcp.add_tool(match_skills)

    def make_tool(skill_name: str, d: Path, unit_ids: list[str], props: dict):
        id_type = Literal[tuple(unit_ids)] if unit_ids else str  # matches tool.json enum
        sit_desc = props.get("situation", {}).get("description", "The user's situation.")
        unit_desc = props.get("unit_id", {}).get("description", "Optional unit id.")

        def run(situation: Annotated[str, Field(description=sit_desc)],
                unit_id: Annotated[Optional[id_type], Field(description=unit_desc)] = None) -> str:  # type: ignore[valid-type]
            pb = (d / "playbook.md").read_text(encoding="utf-8")
            secs = _unit_sections(pb)
            if unit_id:
                if unit_id not in secs:
                    raise ValueError(f"unknown unit_id {unit_id!r} for {skill_name}")
                return secs[unit_id]
            hits = select_units(pb, situation)
            if not hits:
                return (f"NO MATCH: no action unit in {skill_name!r} matches this situation. "
                        "Do not apply this skill; say the situation is outside its triggers. "
                        f"Available units: {', '.join(secs)}.")
            body = "\n\n".join(sec for _, _, sec in hits)
            return (f"Matched {len(hits)} unit(s) by trigger/title overlap (selection only; this tool does not "
                    f"execute the playbook). Check each listed boundary against the user's "
                    f"situation before applying.\n\n{body}")
        return run

    def make_reader(path: Path):
        def reader() -> str:
            return path.read_text(encoding="utf-8")
        return reader

    for n, d in skills.items():
        tool = json.loads((d / "tool.json").read_text(encoding="utf-8"))
        props = tool["input_schema"]["properties"]
        ids = props.get("unit_id", {}).get("enum", [])
        mcp.add_tool(make_tool(n, d, ids, props), name=n, description=tool["description"])

        mcp.resource(f"skillsmith://{n}", name=n, mime_type="text/markdown")(make_reader(d / "SKILL.md"))

    return mcp


def serve(skills_dir: Path) -> None:  # pragma: no cover
    build_server(skills_dir).run()

"""Workspace = the ICM folder. Scaffold, load, stage state, export, router prompt."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

STAGES = ["01_ingest", "02_map", "03_extract", "04_consolidate", "05_write", "06_eval"]
GATES = {"02_map", "04_consolidate"}
TEMPLATES = Path(__file__).parent / "templates"


class WorkspaceError(Exception):
    pass


def scaffold(dest: Path, source: Path) -> "Workspace":
    dest = Path(dest)
    if dest.exists() and any(dest.iterdir()):
        raise WorkspaceError(f"{dest} already exists and is not empty")
    source = Path(source)
    if not source.is_file():
        raise WorkspaceError(f"source not found: {source}")
    shutil.copytree(TEMPLATES, dest, dirs_exist_ok=True)
    for s in STAGES:
        (dest / "stages" / s / "output").mkdir(parents=True, exist_ok=True)
    inp = dest / "stages" / "01_ingest" / "input"
    inp.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, inp / source.name)
    return Workspace(dest)


def load(root: Path) -> "Workspace":
    root = Path(root)
    if not (root / "stages").is_dir() or not (root / "_config").is_dir():
        raise WorkspaceError(f"{root} is not a Skillsmith workspace")
    return Workspace(root)


@dataclass
class Workspace:
    root: Path

    def stage_dir(self, s: str) -> Path:
        return self.root / "stages" / s

    def input(self, s: str) -> Path:
        return self.stage_dir(s) / "input"

    def output(self, s: str) -> Path:
        return self.stage_dir(s) / "output"

    def staging(self, s: str) -> Path:
        return self.stage_dir(s) / "output.staging"

    def done(self, s: str) -> bool:
        return (self.output(s) / "_DONE.json").is_file()

    def approved(self, s: str) -> bool:
        return (self.output(s) / "APPROVED").is_file()

    def config(self, name: str) -> str:
        return (self.root / "_config" / name).read_text(encoding="utf-8")

    def next_pending(self) -> str | None:
        for s in STAGES:
            if not self.done(s):
                return s
        return None

    def status(self) -> list[str]:
        rows = []
        for s in STAGES:
            state = "done" if self.done(s) else "pending"
            gate = ""
            if s in GATES:
                gate = " | gate: " + ("APPROVED" if self.approved(s) else "awaiting approval")
            rows.append(f"{s}: {state}{gate}")
        return rows

    def skill_dirs(self) -> list[Path]:
        out = self.output("05_write")
        if not out.is_dir():
            return []
        return sorted(p for p in out.iterdir() if (p / "SKILL.md").is_file())


def export_skills(w: Workspace, dest: Path) -> list[Path]:
    """Copy finished skill folders. Refuses unless stage 05 and 06 are done."""
    if not (w.done("05_write")):
        raise WorkspaceError("stage 05_write is not done")
    if not w.done("06_eval"):
        raise WorkspaceError("stage 06_eval is not done; run it before exporting")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    dirs = w.skill_dirs()
    clash = [dest / d.name for d in dirs if (dest / d.name).exists()]
    if clash:  # check everything first so a clash never leaves a half-exported set
        raise WorkspaceError(f"{clash[0]} exists; refusing to overwrite")
    out = []
    for d in dirs:
        target = dest / d.name
        shutil.copytree(d, target)
        out.append(target)
    return out


def read_skill_meta(skill_dir: Path) -> tuple[str, str]:
    tool = json.loads((skill_dir / "tool.json").read_text(encoding="utf-8"))
    return tool["name"], tool["description"]


def router_prompt(w_or_dir: "Workspace | Path") -> str:
    if not isinstance(w_or_dir, Workspace) and not Path(w_or_dir).is_dir():
        raise WorkspaceError(f"{w_or_dir} is not a directory")
    dirs = w_or_dir.skill_dirs() if isinstance(w_or_dir, Workspace) else sorted(
        p for p in Path(w_or_dir).iterdir() if (p / "tool.json").is_file())
    lines = ["You can load one skill when a request matches its description.",
             "Reply with the skill name to load its body; otherwise answer normally.", ""]
    for d in dirs:
        name, desc = read_skill_meta(d)
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)

"""Skillsmith modular command registry."""
from __future__ import annotations

from .approve import approve
from .audit_cmd import audit_cmd
from .compile_cmd import compile_cmd
from .config_cmd import config_cmd
from .eval_quality import eval_quality
from .eval_run import eval_run
from .export import export
from .init import init
from .mcp_cmd import mcp_cmd
from .router import router
from .run import run
from .status import status
from .verify_cmd import verify_cmd

ALL = [
    init,
    run,
    approve,
    status,
    verify_cmd,
    audit_cmd,
    compile_cmd,
    export,
    router,
    eval_run,
    eval_quality,
    mcp_cmd,
    config_cmd,
]

__all__ = [
    "ALL",
    "init",
    "run",
    "approve",
    "status",
    "verify_cmd",
    "audit_cmd",
    "compile_cmd",
    "export",
    "router",
    "eval_run",
    "eval_quality",
    "mcp_cmd",
    "config_cmd",
]

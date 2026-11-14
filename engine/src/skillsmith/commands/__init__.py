"""Skillsmith modular command registry."""
from __future__ import annotations

from .init import init
from .run import run
from .approve import approve
from .status import status
from .verify_cmd import verify_cmd
from .audit_cmd import audit_cmd
from .compile_cmd import compile_cmd
from .export import export
from .router import router
from .eval_run import eval_run
from .eval_quality import eval_quality
from .mcp_cmd import mcp_cmd
from .config_cmd import config_cmd

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

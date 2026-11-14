"""MCP serve command: serve skills over Model Context Protocol."""
from __future__ import annotations

from pathlib import Path
import click


@click.command("mcp-serve", help="Serve an exported skills directory over MCP (stdio).")
@click.argument("skills_dir", type=click.Path(path_type=Path, exists=True, file_okay=False))
def mcp_cmd(skills_dir: Path) -> None:
    from ..mcp_server import serve
    serve(skills_dir)

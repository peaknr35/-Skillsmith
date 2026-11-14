"""Round 2: REAL stdio subprocess MCP checks. Usage: python round2_mcp.py <skills_dir> <skillsmith.exe> [skill] situations..."""
import asyncio, sys, json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
SK, EXE = sys.argv[1], sys.argv[2]
async def main():
    params = StdioServerParameters(command=EXE, args=["mcp-serve", SK])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name: t for t in (await s.list_tools()).tools}
            print("tools:", sorted(tools))
            for d in sorted(Path(SK).iterdir()):
                tj = json.loads((d/"tool.json").read_text())
                enum = tools[tj["name"]].inputSchema["properties"]["unit_id"]
                got = enum.get("enum") or [x.get("const") for x in enum.get("anyOf", [])] or enum
                print(d.name, "schema enum == tool.json enum:", got == tj["input_schema"]["properties"]["unit_id"]["enum"], got)
            rl = (await s.list_resources()).resources
            print("resources:", [str(x.uri) for x in rl])
            print("templates:", [x.uriTemplate for x in (await s.list_resource_templates()).resourceTemplates])
            rs = SK and sys.argv[3:]
            for arg in rs:
                skill, sit = arg.split("::",1)
                res = await s.call_tool(skill, {"situation": sit})
                t = res.content[0].text
                units = [l.strip() for l in t.splitlines() if l.startswith("### ")]
                print(f"[{skill}] {sit!r}\n   -> {t.splitlines()[0][:70]} | {units}")
            res = await s.call_tool(sys.argv[3].split("::")[0], {"situation":"x","unit_id":"u02"})
            print("unit_id u02:", res.isError, res.content[0].text.splitlines()[0])
            res = await s.call_tool(sys.argv[3].split("::")[0], {"situation":"x","unit_id":"zzz"})
            print("unit_id bad:", res.isError, res.content[0].text[:100])
asyncio.run(main())

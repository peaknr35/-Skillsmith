import asyncio, sys, json, os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
SK = sys.argv[1]; EXE = sys.argv[2]
async def main():
    params = StdioServerParameters(command=EXE, args=["mcp-serve", SK])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize(); print("server:", init.serverInfo.name, init.protocolVersion)
            tools = await s.list_tools(); print("tools:", [t.name for t in tools.tools])
            for t in tools.tools:
                if t.name == "long-doc-retrieval": print("schema:", json.dumps(t.inputSchema)); print("desc:", t.description[:60])
            res = await s.call_tool("long-doc-retrieval", {"situation": "index a long contract archive"})
            print("call full:", res.isError, res.content[0].text[:80].replace("\n"," | "), len(res.content[0].text))
            res = await s.call_tool("long-doc-retrieval", {"situation": "x", "unit_id": "u02"})
            print("call unit:", res.isError, res.content[0].text[:120].replace("\n"," | "))
            res = await s.call_tool("long-doc-retrieval", {"situation": "x", "unit_id": "nope"})
            print("bad unit:", res.isError, res.content[0].text[:120])
            res = await s.call_tool("get_playbook", {"name": "../x"}); print("traversal name:", res.isError, res.content[0].text[:120])
            res = await s.call_tool("list_skills", {}); print("list_skills:", res.isError, res.content[0].text[:140])
            res = await s.call_tool("get_system_prompt", {"name": "long-doc-retrieval"}); print("sysprompt:", res.content[0].text[:50])
            rl = await s.list_resources(); print("resources:", [str(x.uri) for x in rl.resources])
            rt = await s.list_resource_templates(); print("templates:", [x.uriTemplate for x in rt.resourceTemplates])
            rr = await s.read_resource("skillsmith://long-doc-retrieval"); print("resource:", rr.contents[0].text[:60].replace("\n"," | "))
            try:
                rr = await s.read_resource("skillsmith://..%2F..%2Fetc"); print("resource trav:", rr.contents[0].text[:80])
            except Exception as e: print("resource trav err:", type(e).__name__, str(e)[:100])
asyncio.run(main())

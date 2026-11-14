import asyncio, sys, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
SK, EXE = sys.argv[1:3]
async def main():
    async with stdio_client(StdioServerParameters(command=EXE, args=["mcp-serve", SK])) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for t in (await s.list_tools()).tools:
                if t.name not in ("list_skills","get_playbook","get_system_prompt"):
                    print(t.name, json.dumps(t.inputSchema))
asyncio.run(main())

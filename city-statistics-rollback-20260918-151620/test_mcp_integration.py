import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
from test_database import sample

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        server = StdioServerParameters(command=sys.executable, args=['/home/win10/deer-flow/skills/custom/china-city-statistics/scripts/mcp_server.py'], env={**os.environ, 'CITY_STATISTICS_DB': str(Path(tmp) / 'integration.db')})
        async with stdio_client(server) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {x.name for x in tools.tools} == {'get_city_statistics_schema', 'save_city_statistics', 'query_city_statistics'}
            schema = await session.call_tool('get_city_statistics_schema', {})
            assert not schema.isError
            for value in (1, 2):
                result = await session.call_tool('save_city_statistics', {'records': [sample(value=value)]})
                assert not result.isError, result
            query = await session.call_tool('query_city_statistics', {'city_name': '测试市', 'year': 2024})
            data = json.loads(query.content[0].text)
            assert data['count'] == 1 and data['records'][0]['value'] == 2
            bad = await session.call_tool('save_city_statistics', {'records': [sample(source_quote='')]})
            assert bad.isError
            print('PASS: MCP initialization, typed schema, write, update, query, rejection; isolated temporary DB')

asyncio.run(main())

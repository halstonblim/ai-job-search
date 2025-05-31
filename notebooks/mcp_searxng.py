"""
This tutorial demonstrates how to use the MCP server for SearxNG.
"""
import asyncio
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Using globally installed mcp-searxng
    async with MCPServerStdio(
        params={
            "command": "mcp-searxng",  # Direct command instead of npx
            "env": {"SEARXNG_URL": "http://localhost:8080/"},
            "client_session_timeout_seconds": 25,
        }
    ) as searxng_server:
        
        print("✓ MCP server initialized")
        
        tools = await searxng_server.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        agent = Agent(
            name="Search Assistant",
            instructions="You are a job search assistant using SearxNG. You must use this tool to search the web. ",
            mcp_servers=[searxng_server]
        )
        
        response = await Runner.run(agent,"Search for recent news about Python programming")
        print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
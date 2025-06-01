"""
This tutorial script demonstrates how to use the MCP server for SearxNG to search the web.
"""
import asyncio
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class SearchResults(BaseModel):
    retrieved_date: str
    """The date the search results were retrieved"""

    pageno: int
    """The page number of the search results"""

    query: str
    """The query used to search for job postings"""

    job_titles: list[str]
    """The titles of the job postings"""

    job_urls: list[str]
    """The URLs of the job postings"""
    job_urls: list[str]


async def main():
    # Start the locally installed mcp-searxng server
    async with MCPServerStdio(
        params={
            "command": "mcp-searxng",
            "env": {"SEARXNG_URL": "http://localhost:8080/"},
            "client_session_timeout_seconds": 25,
        }
    ) as searxng_server:
        print("✓ MCP server initialized")
        tools = await searxng_server.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        # Build an agent that knows how to call searxng_web_search
        agent = Agent(
            name="Search Assistant",
            instructions=(
                "When searching for data scientist jobs, ALWAYS use the exact query 'data scientist gh_jid' "
                "with the searxng_web_search tool. Use pageno=1 and language='en'. "
                "Extract job titles and URLs from the search results."
            ),
            mcp_servers=[searxng_server],
            output_type=SearchResults
        )

        response = await Runner.run(agent, "Return a list of data scientist job postings.")
        print("Response:", response)

if __name__ == "__main__":
    asyncio.run(main())

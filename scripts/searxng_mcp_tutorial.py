"""
This tutorial script demonstrates how to use the MCP server for SearxNG to search the web.
The MCP server must be running in the background. Here are the steps to do this locally:

1. Start the MCP server
$docker run -d --name searxng -p 8080:8080 searxng/searxng:latest

2. Get the container id:
$docker ps

3. Enter the shell of the container - we need to make json access allowed
$ docker exec -it <container_id> /bin/bash

4. Edit the settings.yml file to allow json under search -> formats, e.g.
$ vi /etc/searxng/settings.yml # modify the settings.yml file to allow json

5. Restart the container
$ docker restart searxng

6. Confirm that json is allowed
$ curl -i "http://localhost:8080/search?q=hello&format=json"
"""
import asyncio
from agents import Agent, Runner, RunConfig
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

        response = await Runner.run(agent, "Return a list of data scientist job postings.", run_config=RunConfig(workflow_name="Web Search Tutorial"))
        print("Response:", response)

if __name__ == "__main__":
    asyncio.run(main())

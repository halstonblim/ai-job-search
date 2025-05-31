"""
This tutorial script demonstrates how to use the MCP server for SearxNG to read a web page.
"""
from agents import Agent, Runner, function_tool
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
from agents.mcp.server import MCPServerStdio
import requests

load_dotenv()


class RatedJob(BaseModel):
    url: str
    """Url is the url of the job posting"""

    fit: int
    """Fit score is a number between 0 and 5, with 5 being the best fit. A value of -1 means the url is not a job posting."""

    blurb: str
    """Blurb is a short description of the job"""


@function_tool(
    name_override="check_url",
    description_override="Check if the given URL is reachable via a HEAD request and return the status code or error message."
)
def check_url(url: str) -> dict:
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        status = response.status_code
        ok = status < 400
    except Exception as e:
        return "URL is not reachable " + str(e)
    return "URL is reachable status code: " + str(status)


async def main():
    async with MCPServerStdio(
        params={
            "command": "mcp-searxng",
            "env": {"SEARXNG_URL": "http://localhost:8080/"},
            "client_session_timeout_seconds": 25,
        }
    ) as searxng_server:
        print("✓ MCP server initialized")
        
        # The job_searcher agent is not fully implemented in this refactor.
        # We'll pass a dummy search query for now.
        search_query = "data scientist jobs" 
        resume_content = "".join(open('resume.txt', 'r').readlines())

        # Run the manager agent
        results = await run_manager_agent(searxng_server, search_query, resume_content)
        
        for result in results:
            print(f"URL: {result.url}, Fit: {result.fit}, Blurb: {result.blurb}")


if __name__ == "__main__":
    asyncio.run(main())


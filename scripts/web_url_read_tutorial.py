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


INSTRUCTIONS = (
    "Your job is to extract the company, job title, and job description from the URL. "
    "Summarize the requirements, responsibilities, qualifications, software and tools of the job. "
    "Do not include unrelated text such as equal opportunity statements or company descriptions. "
    "If the URL does not contain a job posting, return a short error message explaining why. "
)


async def main(url: str):
    async with MCPServerStdio(
        params={
            "command": "mcp-searxng",
            "env": {"SEARXNG_URL": "http://localhost:8080/"},
            "client_session_timeout_seconds": 25,
        }
    ) as searxng_server:
        print("✓ MCP server initialized")        

        agent = Agent(
            name="ExtractJobDescription",
            instructions=INSTRUCTIONS,
            mcp_servers=[searxng_server],
            model="gpt-4.1-mini",
            )        

        # Run the manager agent
        results = await Runner.run(agent, input=url)
        
        print(results)

if __name__ == "__main__":
    url = "https://www.capitalonecareers.com/job/mclean/senior-manager-data-science-shopping/1732/81260356816"
    asyncio.run(main(url))
"""
This tutorial script demonstrates how to use the Playwright MCP server to read a web page.
"""
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner, RunConfig
from agents.mcp.server import MCPServerStdio

load_dotenv()


class JobDescription(BaseModel):
    company: str
    title: str
    description: str
    requirements: list[str]
    responsibilities: list[str]
    qualifications: list[str]
    tools: list[str]


class PlaywrightWaitServer(MCPServerStdio):
    """Sub-class MCPServerStdio so only specified tools are available."""
    async def list_tools(self):
        all_tools = await super().list_tools()
        return [t for t in all_tools if (t.name in ["browser_wait_for","browser_navigate"])]


MCP_SERVER_PARAMS = {
    "command": "npx",
    "args": [
        "@playwright/mcp@latest",
        "--config", "config.json"
        ],
    "client_session_timeout_seconds": 60,
    }

async def main(url: str):
    async with PlaywrightWaitServer(params=MCP_SERVER_PARAMS) as pw_server:

        print("\nPlaywright MCP server initialized")

        tools = await pw_server.list_tools()

        print(f"\nAvailable tools: {[t.name for t in tools]}")

        INSTRUCTIONS = (
            "Your job extract the company, job title, and job description from the URL. "
            "1. First, navigate to the URL using the browser_navigate tool "
            "2.Examine the output of the browser_navigate tool "
            "- If the text contains a job posting, extract the job description from the snapshot "
            "- If the URL does not contain a job posting, wait for 2 seconds using the browser_wait_for tool and try to extract the job description "
            "3. If the URL does not contain a job posting, return a short error message explaining why. "
            "Summarize the requirements, responsibilities, qualifications, software and tools of the job. "
            "Do not include unrelated text such as equal opportunity statements or company descriptions. "
            "If the URL does not contain a job posting, return a short error message explaining why. "
        )

        agent = Agent(
            name="ExtractJobDescriptionPlaywright",
            instructions=INSTRUCTIONS,
            mcp_servers=[pw_server],
            output_type=JobDescription,
            model="o4-mini",
        )

        results = await Runner.run(agent, input=url, run_config=RunConfig(workflow_name="Playwright MCP Demo"))
        print(f"\n{repr(results.final_output)}")

if __name__ == "__main__":
    test_url = "https://aurora.tech/careers/8014873002?gh_jid=8014873002"
    asyncio.run(main(test_url)) 
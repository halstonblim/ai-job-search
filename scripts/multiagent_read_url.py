"""
This tutorial script demonstrates how to use the MCP server for Playwright MCP to read a web page.
"""
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner, RunContextWrapper, HandoffInputData, handoff, RunConfig, function_tool, ModelSettings
from agents.extensions import handoff_filters
from agents.mcp.server import MCPServerStdio
from typing import Literal
import os

load_dotenv()
os.environ["PLAYWRIGHT_MCP_USE_STDIO"] = "true"


class PlaywrightServer(MCPServerStdio):
    """
    Sub-class MCPServerStdio so only specified tools are available.
    """
    async def list_tools(self):
        all_tools = await super().list_tools()
        return [t for t in all_tools if (t.name in ["browser_wait_for","browser_navigate"])]


NAVIGATE_INSTRUCTIONS = (    
    "Call the browser_navigate tool. "
)

WAIT_FOR_INSTRUCTIONS = (
    "Your job is to wait 5 seconds for the page to load. "
    "NEVER call browser_navigate."
    "Always hand off to the summary agent."
)

SUMMARY_INSTRUCTIONS = (
    "Your job is to summarize the job description or explain why the page is not a job posting. "
)

def _message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    """Filter handoff messages to remove tool content and keep only recent history."""
    data = handoff_filters.remove_all_tools(handoff_message_data)
    history = (
        tuple(handoff_message_data.input_history[-1])
        if isinstance(handoff_message_data.input_history, tuple)
        else handoff_message_data.input_history
    )
    return HandoffInputData(
        input_history=history,
        pre_handoff_items=tuple(data.pre_handoff_items),
        new_items=tuple(data.new_items),
    )

class NavigationOutput(BaseModel):
    job_description: str | None = None
    """The job description if the URL contains a job posting"""

    contains_individual_job_description: bool
    """True if the URL contains a job description"""

    page_description: str
    """A brief description of the page such as job description or company job careers page"""


class JobPageContext(BaseModel):    
    job_description: str | None = None
    """The job description if the URL contains a job posting"""

    contains_individual_job_description: bool | None = None
    """True if the URL contains a job description"""

    page_description: str | None = None
    """A brief description of the page such as job description or company job careers page"""


@function_tool
async def fetch_job_page_context(ctx: RunContextWrapper[JobPageContext]) -> JobPageContext:
    """Fetch the job page context"""
    return ctx.context


async def record_navigation_output(ctx: RunContextWrapper[JobPageContext], navigation_output: NavigationOutput):
    """Record the navigation result for a URL"""
    print("\nRecording to context")
    ctx.context.contains_individual_job_description = navigation_output.contains_individual_job_description
    ctx.context.page_description = navigation_output.page_description
    print("\nContains individual job description: ", navigation_output.contains_individual_job_description)
    print("\nPage description: ", navigation_output.page_description)
    if navigation_output.contains_individual_job_description:
        ctx.context.job_description = navigation_output.job_description

    
async def main(url: str):
    async with PlaywrightServer(
        params={"command": "npx", "args": ["@playwright/mcp@latest", "--config", "config.json"]},
        client_session_timeout_seconds=30,
    ) as pw_server:

        print("\nPlaywright MCP server initialized")

        tools = await pw_server.list_tools()

        print(f"\nAvailable tools: {[t.name for t in tools]}")

        naviation_agent = Agent[JobPageContext](
            name="Navigate",
            instructions=NAVIGATE_INSTRUCTIONS,
            mcp_servers=[pw_server],
            tool_use_behavior="stop_on_first_tool",
            model_settings=ModelSettings(tool_choice='required'),
            model="gpt-4.1-nano",
        )

        wait_agent = Agent[JobPageContext](
            name="Wait",
            instructions=WAIT_FOR_INSTRUCTIONS,
            mcp_servers=[pw_server],
            model_settings=ModelSettings(tool_choice='required'),
            model="gpt-4.1",
        )          

        summary_agent = Agent[JobPageContext](
            name="Summary",
            instructions=SUMMARY_INSTRUCTIONS,
            model="gpt-4.1-mini",
            tools=[fetch_job_page_context],
            tool_use_behavior="stop_on_first_tool",
            model_settings=ModelSettings(tool_choice='required'),
            output_type=JobPageContext,        
        )

        wait_agent.handoffs = [handoff(agent=summary_agent, on_handoff=record_navigation_output, input_type=NavigationOutput)]

        context = JobPageContext()
        await Runner.run(naviation_agent, input=url, context=context, run_config=RunConfig(handoff_input_filter=_message_filter))
        result = await Runner.run(wait_agent, input=url, context=context, run_config=RunConfig(handoff_input_filter=_message_filter))

        print(result.final_output)

if __name__ == "__main__":

    test_url = "https://aurora.tech/careers/8014873002?gh_jid=8014873002"
    test_url = "https://www.capitalonecareers.com/job/mclean/senior-manager-data-science-shopping/1732/81260356816"
    # test_url = "https://www.vectra.ai/about/jobs?gh_jid=6274750"
    asyncio.run(main(test_url)) 
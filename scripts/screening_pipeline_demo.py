"""
This script demonstrates the job screening pipeline given a job posting URL.

The pipeline is as follows:

1. URL Checker agent: Checks if the URL is reachable.
2. Page Inspector agent: Verifies if the page is a single job posting.
3. Extractor agent: Extracts the job description from the URL.
4. Screener agent: Rates the fit of the job posting.
5. Summary agent: Summarizes the job screening results.
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

from agents import Runner, handoff, HandoffInputData, RunConfig
from agents.extensions import handoff_filters
from agents.mcp.server import MCPServerStdio

from job_agents.checker import get_url_checker_agent
from job_agents.inspector import get_page_inspector_agent
from job_agents.extractor import get_extract_description_agent
from job_agents.screener import get_job_screen_agent
from job_agents.summarizer import get_summary_agent
from job_agents.context import (JobScreenContext, 
                                ErrorMessage, 
                                UrlResult, 
                                JobDescription, 
                                FitScore, 
                                InspectionResult, 
                                record_error_on_handoff, 
                                record_url, 
                                record_job_description, 
                                record_fit_score, 
                                record_inspection)

load_dotenv()


def message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    """Clears history"""
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)

    history = (
        tuple(handoff_message_data.input_history[-1:])
        if isinstance(handoff_message_data.input_history, tuple)
        else handoff_message_data.input_history
    )

    return HandoffInputData(
        input_history=history,
        pre_handoff_items=tuple(handoff_message_data.pre_handoff_items),
        new_items=tuple(handoff_message_data.new_items),
    )


async def run_handoff_example(mcp_server, url: str):
    """Define and kickoff the multi-agent handoff chain."""
    # Create the context object
    context = JobScreenContext()
    # Load resume and preferences into context
    context.resume = Path("resume.txt").read_text(encoding='utf-8')
    context.preferences = Path("preferences.txt").read_text(encoding='utf-8')
    
    # Create the agents
    url_checker_agent = get_url_checker_agent()
    page_inspector_agent = get_page_inspector_agent(mcp_server)
    job_extractor_agent = get_extract_description_agent(mcp_server)
    screener_agent = get_job_screen_agent()
    summary_agent = get_summary_agent()
    
    # Define handoffs between agents
    failed_summary_handoff = handoff(agent=summary_agent, on_handoff=record_error_on_handoff, input_type=ErrorMessage)
    url_checker_handoff = handoff(agent=page_inspector_agent, on_handoff=record_url, input_type=UrlResult)
    page_inspector_handoff = handoff(agent=job_extractor_agent, on_handoff=record_inspection, input_type=InspectionResult)
    extractor_handoff = handoff(agent=screener_agent, on_handoff=record_job_description, input_type=JobDescription)
    screener_handoff = handoff(agent=summary_agent, on_handoff=record_fit_score, input_type=FitScore)

    # Add handoffs to agents
    url_checker_agent.handoffs = [url_checker_handoff, failed_summary_handoff]
    page_inspector_agent.handoffs = [page_inspector_handoff, failed_summary_handoff]
    job_extractor_agent.handoffs = [extractor_handoff]
    screener_agent.handoffs = [screener_handoff]
    
    # Start the handoff chain
    print("\nStarting handoff chain...")
    run_config = RunConfig(handoff_input_filter=message_filter, workflow_name="Job Screening Pipeline")
    result = await Runner.run(url_checker_agent, input=url, context=context, run_config=run_config)
    
    return result


class PlaywrightServer(MCPServerStdio):
    """Sub-class MCPServerStdio so only specified tools are available."""
    async def list_tools(self):
        all_tools = await super().list_tools()
        return [t for t in all_tools if (t.name in ["browser_wait_for","browser_navigate"])]


async def main(url: str):
    """
    Main function to test the job screen pipeline on a single job posting

    Args:
        url: The URL of the job posting to screen
    """      
    print(f"\n{'='*60}")
    print(f"Running Job Screening Pipeline\nURL: {url}")
    print('='*60)

    async with PlaywrightServer(
        params={"command": "npx", "args": ["@playwright/mcp@latest", "--config", "config.json"]},
        client_session_timeout_seconds=30,
    ) as pw_server:

        try:
            result = await run_handoff_example(pw_server, url)
            print(f"\n✅ Pipeline complete")
            print(f"\n{result}")
        except Exception as e:
            print(f"\n❌ Pipeline failed\n\n{e}")        
            print("\n" + "-"*40)


if __name__ == "__main__":
    url = "https://www.fanduel.careers/open-positions/senior-data-scientist-6745657?gh_jid=6745657"
    asyncio.run(main(url))
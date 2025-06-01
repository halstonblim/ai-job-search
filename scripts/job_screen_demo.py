"""
This script demonstrates the job screening pipeline given a job posting URL.

The pipeline is as follows:

1. URL vetter agent: Checks if the URL is a job posting.
2. Extractor agent: Extracts the job description from the URL.
3. Screener agent: Rates the fit of the job posting.
4. Summary agent: Summarizes the job screening pipeline.
"""

from agents import Runner, handoff, HandoffInputData
from job_agents.vetter import get_url_vetter_agent
from job_agents.extractor import get_extract_description_agent
from job_agents.screener import get_job_screen_agent
from job_agents.summarizer import get_summary_agent
from job_agents.context import (JobScreenContext, ErrorMessage, UrlResult, JobDescription, FitScore, record_error_on_handoff, record_url, record_job_description, record_fit_score)
from agents.extensions import handoff_filters
from agents.mcp.server import MCPServerStdio

from dotenv import load_dotenv
import asyncio
from pathlib import Path

load_dotenv()

def message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    # First, we'll remove any tool-related messages from the message history
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)

    # Second, we'll also remove the first two items from the history, just for demonstration
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
    """
    Driver function to run the handoff example.
    """
    # Create the context object
    context = JobScreenContext()
    # Load resume and preferences into context
    context.resume = Path("resume.txt").read_text(encoding='utf-8')
    context.preferences = Path("preferences.txt").read_text(encoding='utf-8')
    
    # Create the agents
    vetter_agent = get_url_vetter_agent()
    extractor_agent = get_extract_description_agent(mcp_server)
    screener_agent = get_job_screen_agent()
    summary_agent = get_summary_agent()
    
    # Define handoffs between agents
    failed_summary_handoff = handoff(
        agent=summary_agent,
        on_handoff=record_error_on_handoff,
        input_type=ErrorMessage,
        input_filter=message_filter,
    )
    vetter_handoff = handoff(
        agent=extractor_agent,
        on_handoff=record_url,
        input_type=UrlResult,
        input_filter=message_filter,
    )
    extractor_handoff = handoff(
        agent=screener_agent,
        on_handoff=record_job_description,
        input_type=JobDescription,
        input_filter=message_filter,
    )
    screener_handoff = handoff(
        agent=summary_agent,
        on_handoff=record_fit_score,
        input_type=FitScore,
        input_filter=message_filter,
    )

    # Add handoffs to agents
    vetter_agent.handoffs = [vetter_handoff, failed_summary_handoff]
    extractor_agent.handoffs = [extractor_handoff, failed_summary_handoff]
    screener_agent.handoffs = [screener_handoff]
    
    # Start the handoff chain
    print("\nStarting handoff chain...")
    result = await Runner.run(vetter_agent, input=url, context=context)
    
    return result


async def main(url: str):
    """
    Main function to test the job screen pipeline on a single job posting

    Args:
        url: The URL of the job posting to screen
    """      
    print(f"\n{'='*60}")
    print(f"Running Job Screening Pipeline\nURL: {url}")
    print('='*60)

    async with MCPServerStdio(
        params={
            "command": "mcp-searxng",
            "env": {"SEARXNG_URL": "http://localhost:8080/"},
            "client_session_timeout_seconds": 25,
        }
    ) as searxng_server:
        
        try:
            result = await run_handoff_example(searxng_server, url)
            print(f"\n✅ Pipeline complete")
            print(f"\n{result}")
        except Exception as e:
            print(f"\n❌ Pipeline failed\n\n{e}")        
            print("\n" + "-"*40)

if __name__ == "__main__":
    # working example as of 2025-06-01
    url = "https://job-boards.greenhouse.io/figma/jobs/5364867004?gh_jid=5364867004"  

    # job board (bad) example
    # url = "https://www.capitalonecareers.com/employment/chicago-illinois-united-states-data-science-jobs/234/24980/6252001-4896861-4888671-4887398/4"

    asyncio.run(main(url))
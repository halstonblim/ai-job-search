import asyncio
from typing import List, Dict, Any
from agents import Agent, Runner, handoff, HandoffInputData
from pydantic import BaseModel
from job_agents.vetter import get_url_vetter_agent
from job_agents.extractor import get_extract_description_agent
from job_agents.screener import get_job_screen_agent
from job_agents.summarizer import get_summary_agent, SummaryAgentOutput
from job_agents.context import JobScreenContext, ErrorMessage, record_error_on_handoff
from agents.extensions import handoff_filters

# Assuming job_searcher agent is defined elsewhere and returns a list of URLs
# from job_agents.job_searcher import get_job_searcher_agent, JobSearcherOutput 

class ManagerAgentInput(BaseModel):
    search_query: str
    resume: str


def message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    """Filter handoff messages to remove tool-related content and keep only recent history."""
    # First, remove any tool-related messages from the message history
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)

    # Keep only the last message for cleaner handoffs
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


async def screen_single_job(mcp_server, url: str) -> SummaryAgentOutput:
    """
    Screen a single job posting URL through the complete pipeline.
    
    Args:
        mcp_server: The MCP server instance for web operations
        url: The job posting URL to screen
        
    Returns:
        result: a SummaryAgentOutput object containing
        - url: The job posting URL
        - fit_score: The fit score of the job posting
        - reason: The reason for the fit score
        - job_description: The job description
        - failed: Whether the job screening pipeline failed
        - error_message: The error message from the job screening pipeline
    """
    try:
        # Create fresh context for this job
        context = JobScreenContext()
        
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
            input_filter=message_filter
        )
        vetter_handoff = handoff(agent=extractor_agent, input_filter=message_filter)
        extractor_handoff = handoff(agent=screener_agent, input_filter=message_filter)
        summary_handoff = handoff(agent=summary_agent, input_filter=message_filter)

        # Configure agent handoffs
        vetter_agent.handoffs = [vetter_handoff, failed_summary_handoff]
        extractor_agent.handoffs = [extractor_handoff, failed_summary_handoff]
        screener_agent.handoffs = [summary_handoff]
        
        # Run the handoff chain
        result = await Runner.run(vetter_agent, input=url, context=context)
        
        # Extract results from context and result
        return result.final_output
        
    except Exception as e:
        return SummaryAgentOutput(
            url=url,
            company="",
            title="",
            fit_score=0,
            reason=f"Processing failed: {str(e)}",
            failed=True,
            error_message=str(e)
        )


async def screen_multiple_jobs(mcp_server, urls: List[str]) -> Dict[str, Any]:
    """
    Screen multiple job postings in parallel using asyncio.gather.
    
    Args:
        mcp_server: The MCP server instance for web operations
        urls: List of job posting URLs to screen
        
    Returns:
        Dictionary containing all results and summary statistics
    """
    print(f"\nStarting parallel screening of {len(urls)} job postings...")
    
    # Run all job screenings in parallel
    tasks = [screen_single_job(mcp_server, url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # Process results - screen_single_job always returns SummaryAgentOutput
    successful_results = []
    failed_results = []
    
    for result in results:
        if result.failed:
            failed_results.append(result)
        else:
            successful_results.append(result)
    
    # Calculate summary statistics
    fit_scores = [r.fit_score for r in successful_results if r.fit_score >= 0]
    avg_fit_score = sum(fit_scores) / len(fit_scores) if fit_scores else 0
    
    # Sort successful results by fit score (highest first)
    successful_results.sort(key=lambda x: x.fit_score, reverse=True)
    
    # Compile final results
    final_results = {
        "total_processed": len(urls),
        "successful_screenings": len(successful_results),
        "failed_screenings": len(failed_results),
        "average_fit_score": round(avg_fit_score, 2),
        "best_matches": successful_results[:5],  # Top 5 matches
        "all_successful_results": successful_results,
        "failed_results": failed_results,
        "summary": {
            "high_fit_jobs": len([r for r in successful_results if r.fit_score >= 4]),
            "medium_fit_jobs": len([r for r in successful_results if 2 <= r.fit_score < 4]),
            "low_fit_jobs": len([r for r in successful_results if 1 <= r.fit_score < 2]),
            "unreachable_urls": len(failed_results)
        }
    }
    
    print(f"\n✅ Screening complete!")
    print(f"Successfully processed: {final_results['successful_screenings']}/{final_results['total_processed']}")
    print(f"Average fit score: {final_results['average_fit_score']}")
    print(f"High fit jobs (4-5): {final_results['summary']['high_fit_jobs']}")
    print(f"Medium fit jobs (2-3): {final_results['summary']['medium_fit_jobs']}")
    print(f"Low fit jobs (0-1): {final_results['summary']['low_fit_jobs']}")
    
    return final_results


async def run_manager_agent(mcp_server, search_query: str, resume: str = None, urls: List[str] = None):
    """
    Main manager function that orchestrates the job screening pipeline.
    
    Args:
        mcp_server: The MCP server instance for web operations
        search_query: The search query (for future job search integration)
        resume: Resume content (currently loaded from file in screener agent)
        urls: Optional list of URLs to process. If None, uses default examples.
        
    Returns:
        Dictionary containing all screening results and statistics
    """
    # For now, use example URLs if none provided
    # In the future, this would integrate with a job searcher agent
    if urls is None:
        urls = [
            "https://job-boards.greenhouse.io/figma/jobs/5364867004?gh_jid=5364867004",
            "https://www.capitalonecareers.com/employment/chicago-illinois-united-states-data-science-jobs/234/24980/6252001-4896861-4887398-4887398/4",
            "https://careers.google.com/jobs/results/1234567890"  # Example non-existent URL
        ]
    
    print(f"\n{'='*60}")
    print(f"Job Screening Manager")
    print(f"Search Query: {search_query}")
    print(f"URLs to Process: {len(urls)}")
    print('='*60)
    
    # Run parallel job screening
    final_results = await screen_multiple_jobs(mcp_server, urls)
    
    return final_results 
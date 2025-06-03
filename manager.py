"""
Manager script orchestrating the job search and screening pipeline.
"""
import argparse
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from agents import Runner, handoff, HandoffInputData, RunConfig
from agents.mcp.server import MCPServerStdio
from scripts.screening_pipeline_demo import PlaywrightServer
from agents.extensions import handoff_filters
from urllib.parse import urlparse

from job_agents.searcher import build_job_searcher_agent, SearchResults
from job_agents.checker import get_url_checker_agent
from job_agents.inspector import get_page_inspector_agent
from job_agents.extractor import get_extract_description_agent
from job_agents.screener import get_job_screen_agent
from job_agents.summarizer import get_summary_agent
from job_agents.context import (JobScreenContext,
                                ErrorMessage,
                                UrlResult,
                                InspectionResult,
                                JobDescription,
                                FitScore,
                                SummaryAgentOutput,
                                record_error_on_handoff,
                                record_url,
                                record_inspection,
                                record_job_description,
                                record_fit_score)


class JobSearchManager:
    """Orchestrates the job search and screening workflow."""
    def __init__(self, 
                 job_title: str, 
                 resume_path: str, 
                 preferences_path: str, 
                 urls: Optional[List[str]] = None,
                 top_n: Optional[int] = None,
                 search_only: bool = False):
        self.job_title = job_title
        self.resume_path = resume_path
        self.preferences_path = preferences_path
        self.urls = urls
        self.top_n = top_n
        self.search_only = search_only

    def _message_filter(self, handoff_message_data: HandoffInputData) -> HandoffInputData:
        """Filter handoff messages to remove tool content and keep only recent history."""
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

    async def _screen_single_job(self, url: str) -> SummaryAgentOutput:
        """Screen a single job URL through the full pipeline."""
        async with PlaywrightServer(
            params={"command": "npx", "args": ["@playwright/mcp@latest", "--config", "playwright_config/config.json"]},
            client_session_timeout_seconds=30,
        ) as server:
            try:
                # Create the context object
                context = JobScreenContext()
                # Load resume and preferences into context
                context.resume = Path(self.resume_path).read_text(encoding='utf-8')
                context.preferences = Path(self.preferences_path).read_text(encoding='utf-8')

                # Create the agents
                url_checker_agent = get_url_checker_agent()
                page_inspector_agent = get_page_inspector_agent(server)
                job_extractor_agent = get_extract_description_agent(server)
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
                domain_name = urlparse(url).netloc.replace("www.", "").split(".")[-2] # domain name before .com/org/etc
                workflow_name = f"{domain_name} job screen"
                run_config = RunConfig(handoff_input_filter=self._message_filter, workflow_name=workflow_name)
                result = await Runner.run(url_checker_agent, input=url, context=context, run_config=run_config)

                return result.final_output
            except Exception as e:
                return SummaryAgentOutput(
                    url=url,
                    company="",
                    title="",
                    fit_score=0,
                    reason=f"Processing failed: {e}",
                    failed=True,
                    error_message=str(e)
                )

    async def screen_multiple_jobs(self, urls: List[str]) -> Dict[str, Any]:
        """Run screening of multiple job URLs in parallel and summarize results."""
        print(f"\nStarting parallel screening of {len(urls)} job postings...")
        tasks = [self._screen_single_job(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

    async def search_jobs(self, server) -> List[str]:
        """Runs the search agent to retrieve a list of job URLs."""
        agent = build_job_searcher_agent(self.job_title)
        agent.mcp_servers = [server]
        result = await Runner.run(agent, self.job_title)
        search_results: SearchResults = result.final_output
        return search_results.job_urls

    def compile_report(self, raw_results: Dict[str, Any]):
        """Prints a short summary report of the screening results."""
        successful = [r for r in raw_results if not getattr(r, "failed", False)]
        failed = [r for r in raw_results if getattr(r, "failed", False)]
        scores = [r.fit_score for r in successful if r.fit_score >= 0]
        avg = sum(scores) / len(scores) if scores else 0
        successful.sort(key=lambda x: x.fit_score, reverse=True)
        summary = {
            "high_fit_jobs": len([r for r in successful if r.fit_score >= 4]),
            "medium_fit_jobs": len([r for r in successful if 2 <= r.fit_score < 4]),
            "low_fit_jobs": len([r for r in successful if 1 <= r.fit_score < 2]),
            "unreachable_urls": len(failed)
        }
        results = {
            "total_processed": len(raw_results),
            "successful_screenings": len(successful),
            "failed_screenings": len(failed),
            "average_fit_score": round(avg, 2),
            "summary": summary
        }        
        total = results.get("total_processed", 0)
        success = results.get("successful_screenings", 0) 
        failed = results.get("failed_screenings", 0)
        avg_score = results.get("average_fit_score", 0)
        summary = results.get("summary", {})
        high = summary.get("high_fit_jobs", 0)
        medium = summary.get("medium_fit_jobs", 0)
        low = summary.get("low_fit_jobs", 0)

        print("\n" + "=" * 60)
        print("JOB SCREENING REPORT")
        print("=" * 60)
        print(f"Total jobs processed:    {total}")
        print(f"Successful screenings:   {success}")
        print(f"Failed screenings:       {failed}")
        print(f"Average fit score:       {avg_score}")
        print(f"High fit jobs (4-5):     {high}")
        print(f"Medium fit jobs (2-3):   {medium}")
        print(f"Low fit jobs (1-2):      {low}")

    async def run(self) -> Dict[str, Any]:
        """Main entrypoint for running the manager."""
        async with MCPServerStdio(
            params={
                "command": "mcp-searxng",
                "env": {"SEARXNG_URL": "http://localhost:8080/", "SEARXNG_MCP_TIMEOUT": "30"},
                "client_session_timeout_seconds": 25,
            }
        ) as searxng_server:
            # Determine URLs to process
            if self.urls:
                print("\nManual override: using provided URLs and skipping search agent")
                print(f"URLs: {self.urls}")
                urls = self.urls
            else:
                print("\nSearching for jobs...",end="")
                urls = await self.search_jobs(searxng_server)
                print(f"Found {len(urls)} job URLs")
            # Limit to top N if specified
            if self.top_n is not None:
                print(f"\nLimiting screening to top {self.top_n} URLs")
                urls = urls[: self.top_n]
            if self.search_only:
                print("\nSearch only mode: found URLs:")
                for url in urls:
                    print(url)
                return {"urls": urls}

            # Run the screening pipeline via separate Playwright MCP server per URL
            results = await self.screen_multiple_jobs(urls)
            self.compile_report(results)
            return results 
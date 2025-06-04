"""
Manager script orchestrating the job search and screening pipeline.
"""
import argparse
import asyncio
import logging
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
                 desired_count: Optional[int] = None,
                 search_only: bool = False,
                 batch_size: int = 5):
        self.job_title = job_title
        self.resume_path = resume_path
        self.preferences_path = preferences_path
        self.urls = urls
        self.desired_count = desired_count
        self.search_only = search_only
        self.batch_size = batch_size

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
            client_session_timeout_seconds=60,
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
                domain_name = urlparse(url).netloc.replace("www.", "").split(".")[-2] # domain name before .com/org/etc
                workflow_name = f"{domain_name} job screen"
                logging.info(f"Starting handoff chain for {workflow_name}...")
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

    async def screen_multiple_jobs(self, urls: List[str]) -> List[SummaryAgentOutput]:
        """Run screening of multiple job URLs in parallel, continuing on individual errors."""
        # Launch screening tasks concurrently, allowing individual failures to be caught
        tasks = [asyncio.create_task(self._screen_single_job(url)) for url in urls]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        # Normalize results: wrap any unexpected outputs or exceptions as failed SummaryAgentOutput
        final_results: List[SummaryAgentOutput] = []
        for url, result in zip(urls, raw_results):
            if isinstance(result, Exception) or not isinstance(result, SummaryAgentOutput):
                logging.error(f"Error screening {url}: {result}", exc_info=True)
                final_results.append(SummaryAgentOutput(
                    url=url,
                    company="",
                    title="",
                    fit_score=0,
                    reason=f"Processing failed: {result}",
                    failed=True,
                    error_message=str(result)
                ))
            else:
                final_results.append(result)
        return final_results

    async def screen_jobs_in_batches(self, urls: List[str]) -> List[SummaryAgentOutput]:
        """Screen URLs in batches respecting the batch_size setting."""
        all_results: List[SummaryAgentOutput] = []
        for i in range(0, len(urls), self.batch_size):
            batch_number = i // self.batch_size + 1
            batch = urls[i : i + self.batch_size]
            logging.info(f"Starting batch {batch_number} of parallel screening of {len(batch)} job postings")
            successful_count = len([r for r in all_results if not getattr(r, 'failed', False)])
            logging.info(f"Current successful job screens: {successful_count}")
            batch_results = await self.screen_multiple_jobs(batch)
            all_results.extend(batch_results)
            if self.desired_count is not None:
                successful = [r for r in all_results if not getattr(r, 'failed', False)]
                if len(successful) >= self.desired_count:
                    break
        return all_results

    async def search_jobs(self, server, pageno: int = 1) -> List[str]:
        """Run the search agent for a given page number."""
        agent = build_job_searcher_agent(self.job_title, pageno)
        agent.mcp_servers = [server]
        logging.info(f"Searching for jobs (page {pageno})...")
        result = await Runner.run(agent, self.job_title, run_config=RunConfig(workflow_name=f"search page {pageno}"))
        search_results: SearchResults = result.final_output
        return search_results.job_urls

    def compile_report(self, raw_results: Dict[str, Any]) -> str:
        """Return a short summary report of the screening results."""
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

        lines = [
            "",
            "=" * 60,
            "JOB SCREENING REPORT",
            "=" * 60,
            f"Total jobs processed:    {total}",
            f"Successful screenings:   {success}",
            f"Failed screenings:       {failed}",
            f"Average fit score:       {avg_score}",
            f"High fit jobs (4-5):     {high}",
            f"Medium fit jobs (2-3):   {medium}",
            f"Low fit jobs (1-2):      {low}",
        ]
        return "\n".join(lines)

    async def run(self) -> Dict[str, Any]:
        """Main entrypoint for running the manager."""
        async with MCPServerStdio(
            params={
                "command": "mcp-searxng",
                "env": {"SEARXNG_URL": "http://localhost:8080/", "SEARXNG_MCP_TIMEOUT": "240"},
                "client_session_timeout_seconds": 240,
            }
        ) as searxng_server:
            if self.urls:
                logging.info("Manual override: using provided URLs and skipping search agent")
                urls = self.urls
                if self.search_only:
                    logging.info("Search only mode: found URLs:")
                    for url in urls:
                        logging.info(url)
                    logging.info("Job Search Completed")
                    return {"urls": urls}
                results = await self.screen_jobs_in_batches(urls)
                logging.info("Job Search Completed")
                return results

            # Automatic search mode
            page = 1
            pending_urls: List[str] = []
            results: List[SummaryAgentOutput] = []
            successful = 0
            batch_number = 0

            while True:
                if not pending_urls:
                    new_urls = await self.search_jobs(searxng_server, page)
                    logging.info(f"Found {len(new_urls)} job URLs")
                    if not new_urls:
                        break
                    pending_urls.extend(new_urls)
                    page += 1

                batch = pending_urls[: self.batch_size]
                pending_urls = pending_urls[self.batch_size:]
                batch_number += 1
                logging.info(f"Starting batch {batch_number} of parallel screening of {len(batch)} job postings")
                logging.info(f"Current successful job screens: {successful}")
                batch_results = await self.screen_multiple_jobs(batch)
                results.extend(batch_results)
                successful += len([r for r in batch_results if not getattr(r, 'failed', False)])

                if self.search_only:
                    continue
                if self.desired_count is not None and successful >= self.desired_count:
                    break

            if self.search_only:
                logging.info("Search only mode: found URLs:")
                for url in [r.url for r in results]:
                    logging.info(url)
                logging.info("Job Search Completed")
                return {"urls": [r.url for r in results]}
            logging.info("Job Search Completed")
            return results

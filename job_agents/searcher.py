from agents import Agent
from pydantic import BaseModel
from typing import List


class SearchResults(BaseModel):
    retrieved_date: str
    """The date the search results were retrieved"""
    
    pageno: int
    """The page number of the search results"""

    query: str
    """The query used to search for job postings"""
    
    job_urls: List[str]
    """The URLs of the job postings"""


def build_job_searcher_agent(query: str):
    INSTRUCTIONS = (
        f"You job is to search for {query} jobs. "
        "When searching, use the web_search tool and ALWAYS use the exact query "
        f"{query} gh_jid' with pageno=1 and language='en'. "
        "Extract a list of URLs from the search results and store in the SearchResults.job_urls field. "
        "Only include URLs with a job id parameter like 'gh_jid' in the URL. "
    )
    return Agent(
        name="Job Search Agent",
        instructions=INSTRUCTIONS,
        model="gpt-4.1-mini",
        output_type=SearchResults
    ) 
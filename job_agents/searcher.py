
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

    job_titles: List[str]
    """The titles of the job postings"""
    
    job_urls: List[str]
    """The URLs of the job postings"""


INSTRUCTIONS = (
    "When searching for data scientist jobs, ALWAYS use the exact query 'data scientist gh_jid' "
    "with the searxng_web_search tool. Use pageno=1 and language='en'. "
    "Extract job titles and URLs from the search results. "
    "Return the results in the specified SearchResults format."
)


def build_job_searcher_agent() -> Agent:
    return Agent(
        name="Job Search Agent",
        instructions=INSTRUCTIONS,
        model="gpt-4.1-mini",
        output_type=SearchResults
    ) 
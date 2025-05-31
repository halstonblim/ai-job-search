from agents import Agent
from pydantic import BaseModel
from .context import JobScreenContext, fetch_fit_score, fetch_error_message, fetch_job_description
from typing import Literal


class SummaryAgentOutput(BaseModel):
    url: str
    """The URL of the job posting"""

    company: str
    """The company name"""

    title: str
    """The job title"""

    fit_score: Literal[0,1,2,3,4,5]
    """The fit score of the job posting."""

    reason: str
    """Reason for the fit score"""

    failed: bool
    """Whether the job screening failed"""

    error_message: str
    """Any error message"""


def get_summary_agent():
    return Agent[JobScreenContext](
        name="SummaryAgent",
        instructions="Your job is to summarize the job search pipeline and any error messages.",
        output_type=SummaryAgentOutput,
        tools=[fetch_fit_score, fetch_error_message, fetch_job_description]
    ) 
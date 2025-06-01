from agents import Agent
from .context import JobScreenContext, record_job_description


INSTRUCTIONS = (
    "Your job is to extract the company, job title, and job description from the URL. "
    "Summarize the requirements, responsibilities, qualifications, software and tools of the job. "
    "Do not include unrelated text such as equal opportunity statements or company descriptions. "
    "If the URL does not contain a job posting, simply hand off to the summarizer agent with an error message explaining why. "
    "After you are done, hand off to the screener agent. "
    )


def get_extract_description_agent(mcp_server):
    return Agent[JobScreenContext](
        name="ExtractJobDescription",
        instructions=INSTRUCTIONS,
        mcp_servers=[mcp_server],
        model="gpt-4.1-mini",
    ) 
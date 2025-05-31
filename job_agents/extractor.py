from agents import Agent
from .context import JobScreenContext, record_job_description


INSTRUCTIONS = (
    "Your job is to extract the company, title, and job description from the URL and record it in the context. "
    "Include every detail about the job including requirements, responsibilities, qualifications, software and tools mentioned. "
    "Do not include any other unrelated text such as equal opportunity statements, company descriptions. "
    "If the URL does not contain a job posting, simply hand off to the summarizer agent with an error message explaining why. "
    "After you are done, hand off to the screener agent. "
)

def get_extract_description_agent(mcp_server):
    return Agent[JobScreenContext](
        name="ExtractJobDescription",
        instructions=INSTRUCTIONS,
        mcp_servers=[mcp_server],
        tools=[record_job_description],
    ) 
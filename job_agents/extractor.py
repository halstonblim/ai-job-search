from agents import Agent, ModelSettings
from .context import JobScreenContext


INSTRUCTIONS = (
    "ALWAYS call browser_wait_for to wait 10 seconds for the page to load. \n"
    "NEVER call browser_navigate, the page is already loaded. \n"
    "Extract the company, job title, and job description, including requirements, responsibilities, qualifications, software and tools. \n"
    "Do not include irrelevant text such as equal opportunity statements or company descriptions. \n"
    "ALWAYS hand off to the screener agent. \n"
    )


def get_extract_description_agent(mcp_server):
    return Agent[JobScreenContext](
        name="ExtractJobDescription",
        instructions=INSTRUCTIONS,
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice='required'),
        model="gpt-4.1-mini",
    ) 
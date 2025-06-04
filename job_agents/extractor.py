from agents import Agent, ModelSettings
from .context import JobScreenContext


INSTRUCTIONS = (
    "ALWAYS call browser_wait_for to wait 10 seconds for the page to load. \n"
    "NEVER call browser_navigate, the page is already loaded. \n"
    "Extract the following information if available: \n"
    "- company \n"
    "- job title \n"
    "- location, hybrid, or remote \n"
    "- type of role (full-time, part-time, contract, internship, etc.) \n"
    "- work experience needed, or fresh grad role \n"
    "- responsibilities \n"
    "- education or degree requirements \n"
    "- any software and tools mentioned \n\n"
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
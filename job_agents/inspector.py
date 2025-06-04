from agents import Agent, ModelSettings
from .context import JobScreenContext, InspectionResult


INSTRUCTIONS = (    
    "Navigate to the URL. NEVER call browser_wait_for. \n"
    "ALWAYS perform EXACTLY one of the following actions: \n"
    "1. If the page is not a single job description, handoff to the summarizer. \n"
    "2. If the page contains a single job description, handoff to the job extractor. \n"
)


def get_page_inspector_agent(mcp_server):
    return Agent[JobScreenContext](
        name="PageInspector",
        instructions=INSTRUCTIONS,
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice='required'),
        model="gpt-4o-mini",
        output_type=InspectionResult
    ) 
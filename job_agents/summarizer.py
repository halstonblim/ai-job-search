from agents import Agent, ModelSettings
from .context import JobScreenContext, SummaryAgentOutput, fetch_job_screen_result


INSTRUCTIONS = "Fetch the result of the job screening"


def get_summary_agent():
    return Agent[JobScreenContext](
        name="SummaryAgent",
        instructions=INSTRUCTIONS,
        tools=[fetch_job_screen_result],
        tool_use_behavior="stop_on_first_tool",
        model_settings=ModelSettings(tool_choice='required'),
        output_type=SummaryAgentOutput,
        model="gpt-4.1-nano",
    ) 
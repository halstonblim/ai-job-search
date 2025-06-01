from agents import Agent, ModelSettings
from .context import JobScreenContext, fetch_job_and_user_info


def get_job_screen_agent() -> Agent[JobScreenContext]:
    """Builds the job screening agent with dynamic resume content."""    


    INSTRUCTIONS = (
        "You are a job screening agent. Your task is to:\n"
        "1. First, fetch the job and user information from the context\n"
        "2. Analyze how well the job description matches the resume and preferences\n"
        "3. Rate the fit of the job between 1 and 5 (1=poor fit, 5=excellent fit)\n"
        "4. Always hand off the result to the summary agent"
    )


    return Agent[JobScreenContext](
        name="JobScreen",
        instructions=INSTRUCTIONS,
        tools=[fetch_job_and_user_info],
        model_settings=ModelSettings(tool_choice='required'),
        model="gpt-4.1-mini"
    ) 
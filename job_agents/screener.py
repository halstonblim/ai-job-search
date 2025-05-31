from agents import Agent
from .context import JobScreenContext, record_fit_score, fetch_job_description


INSTRUCTIONS = (
    "Given a job description, resume, and preferences, rate the fit of the job between 1 and 5. "
    "Update the context with the fit score and fit reason. "
    "Always hand off the result to the summary agent. "
    "\n\n"
    "Resume:\n\n"
    f"{"\n".join(open('resume.txt','r').readlines())}\n\n"
    "Preferences:"
    "- No significant software engineering experience"
    "- Less than 7 years of work experience"
)


def get_job_screen_agent():
    return Agent[JobScreenContext](
        name="JobScreen",
        instructions=INSTRUCTIONS,
        tools=[record_fit_score, fetch_job_description],
    ) 
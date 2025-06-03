from pydantic import BaseModel
from agents import RunContextWrapper, function_tool, ToolsToFinalOutputResult, FunctionToolResult
from typing import Literal
import textwrap


class JobScreenContext(BaseModel):
    """
    Defines the local context for the job screening agent. 
    The local context is not directly available to the LLM.
    Context fields are updated by each agent in the pipeline at handoff points.
    """
    resume: str = None
    """The resume of the user"""

    preferences: str = None
    """The preferences of the user"""

    url: str = None
    """The URL of the job posting"""

    company: str = None
    """The company name"""

    title: str = None
    """The job title"""

    job_description: str = None
    """The job description"""

    fit_score: Literal[0,1,2,3,4,5] = None
    """The fit score of the job posting"""

    reason: str = None
    """A short explanation of the fit score"""

    failed: bool = False
    """The status of the job screening agent."""

    error_message: str = None
    """Any error message"""


class SummaryAgentOutput(BaseModel):
    """
    The output of the job screening agent.
    Custom formatting for print output.
    """
    url: str | None = None
    company: str | None = None
    title: str | None = None
    fit_score: Literal[0,1,2,3,4,5] | None = None
    reason: str | None = None
    failed: bool | None = False
    error_message: str | None = None

    def __repr__(self) -> str:
        title = self.title or ""
        company = self.company or ""
        title_company = f"{title} at {company}" if (title and company) else ""
        url = self.url or ""
        fit_score = self.fit_score if self.fit_score is not None else ""
        reason = self.reason or ""
        failed = self.failed
        error_message = self.error_message or ""
        lines = [
            f"url:            {url}",
            f"title:          {title_company}",
            f"fit_score:      {fit_score}",
            "reason:",
        ]
        if reason:
            wrapped = textwrap.wrap(reason, width=80)
            for wr in wrapped:
                lines.append(f"    {wr}")
        else:
            lines.append("    ")
        lines.append(f"failed:         {failed}")
        lines.append("error_message:")
        if error_message:
            wrapped_err = textwrap.wrap(error_message, width=80)
            for wr in wrapped_err:
                lines.append(f"    {wr}")
        else:
            lines.append("    ")
        return "\n".join(lines)


# Tools to make local context available to the LLM


@function_tool
async def fetch_job_and_user_info(ctx: RunContextWrapper[JobScreenContext]) -> dict:
    """Fetch the job description, resume, and preferences from the context"""
    return {"job_description": ctx.context.job_description, 
            "resume": ctx.context.resume, 
            "preferences": ctx.context.preferences}


@function_tool
async def fetch_job_screen_result(ctx: RunContextWrapper[JobScreenContext]) -> SummaryAgentOutput:
    """Fetch the job screening result from the context"""
    return SummaryAgentOutput(
        url=ctx.context.url,
        company=ctx.context.company,
        title=ctx.context.title,
        fit_score=ctx.context.fit_score,
        reason=ctx.context.reason,
        failed=ctx.context.failed,
        error_message=ctx.context.error_message)


# Handoff functions and handoff input types


class ErrorMessage(BaseModel):
    message: str
    """The error message"""


class FitScore(BaseModel):
    fit_score: Literal[1,2,3,4,5]
    """The fit score of the job posting"""

    reason: str
    """The reason for the fit score"""


class JobDescription(BaseModel):
    company: str
    """The company name"""

    title: str
    """The job title"""

    job_description: str
    """The job description"""


class UrlResult(BaseModel):
    url: str
    """The URL of the job posting"""


class InspectionResult(BaseModel):
    page_is_single_job: bool
    """Whether the page is a single job description"""

    inspection_reason: str
    """The reason why the page is or is not a single job description"""


async def record_inspection(ctx: RunContextWrapper[JobScreenContext], inspection: InspectionResult):
    """Record the inspection in the context"""
    # print(f"\nPassed inspection result:\n\n{repr(inspection)}")


async def record_url(ctx: RunContextWrapper[JobScreenContext], url: UrlResult):
    """Record the URL in the context"""
    ctx.context.url = url.url


async def record_job_description(ctx: RunContextWrapper[JobScreenContext], job_description: JobDescription):
    """Record the job description in the context"""
    ctx.context.company = job_description.company
    ctx.context.title = job_description.title
    ctx.context.job_description = job_description.job_description
    # print(f"\nRecorded job description in context:\n\n{repr(job_description.job_description)}")


async def record_fit_score(ctx: RunContextWrapper[JobScreenContext], fit_score: FitScore):
    """Record the fit score and fit reason in the context"""
    ctx.context.fit_score = fit_score.fit_score
    ctx.context.reason = fit_score.reason
    # print(f"\nRecorded fit score in context:\n\n{repr(fit_score)}")


async def record_error_on_handoff(ctx: RunContextWrapper[JobScreenContext], error_message: ErrorMessage):
    """Record the error message in the context"""
    ctx.context.error_message = error_message.message
    ctx.context.failed = True
    print(f"\n⚠️ Unable to screen job posting:\n\n{repr(error_message)}")
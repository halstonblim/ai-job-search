from pydantic import BaseModel
from agents import RunContextWrapper, function_tool
from typing import Literal


class JobScreenContext(BaseModel):
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


class ErrorMessage(BaseModel):
    message: str
    """The error message"""


@function_tool
async def fetch_fit_score(ctx: RunContextWrapper[JobScreenContext]) -> str:
    """
    Fetch the fit score and fit reason from the context
    """
    if (ctx.context.fit_score is None) or (ctx.context.reason is None):
        return "No fit score found. "
    return f"Fit score: {ctx.context.fit_score}, reason: {ctx.context.reason}"


@function_tool
async def fetch_job_description(ctx: RunContextWrapper[JobScreenContext]) -> str:
    """
    Fetch the job description from the context
    """
    return ctx.context.job_description


@function_tool
async def fetch_error_message(ctx: RunContextWrapper[JobScreenContext]) -> str:
    """
    Fetch error message and failed status from the context
    """
    if (not ctx.context.failed) and (not ctx.context.error_message):
        return "No errors"
    return f"Failed: true, Error message: {ctx.context.error_message}"


@function_tool
async def record_fit_score(ctx: RunContextWrapper[JobScreenContext], fit_score: int, reason: str):
    """
    Record the fit score and fit reason in the context

    Args: 
        fit_score: The fit score of the job posting
        reason: The reason for the fit score
    """
    ctx.context.fit_score = fit_score
    ctx.context.reason = reason
    print("\nRecorded the fit score and fit reason in the context")


@function_tool
async def record_job_description(ctx: RunContextWrapper[JobScreenContext], job_description: str):
    """
    Record the job description in the context
    """
    ctx.context.job_description = job_description
    print("\nRecorded the job description in the context")


async def record_error_on_handoff(ctx: RunContextWrapper[JobScreenContext], error_message: ErrorMessage):
    """
    Record the error message in the context
    """
    ctx.context.error_message = error_message.message
    ctx.context.failed = True
    print("\n⚠️ Warning: Job screening failed. Error message recorded in context")
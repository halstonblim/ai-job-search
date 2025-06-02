from agents import Agent, function_tool, ModelSettings
from pydantic import BaseModel
import requests
from .context import JobScreenContext


class UrlVetterOutput(BaseModel):
    url: str
    """The url after any redirects"""

    status_code: int
    """The status code of the get request"""

    reachable: bool
    """Whether the url is reachable"""

    error_message: str | None = None
    """The error message if the url is not reachable"""


@function_tool
def check_url_reachability(url: str) -> dict:
    """
    Check if the given URL is reachable with a GET request and return the status code.

    Args:
        url: The URL to check  

    Returns:
        A dictionary containing the URL, status code, and error message
    """
    try:
        resp = requests.get(
            url,
            allow_redirects=True,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return {
            "url": resp.url,        # final URL after redirects
            "status_code": resp.status_code,
            "reachable": resp.ok,   # True if 200 ≤ status < 400
            "error_message": None,
        }
    except requests.RequestException as e:
        return {
            "url": url,
            "status_code": -1,
            "reachable": False,
            "error_message": str(e),
        }


INSTRUCTIONS = (
    "Check if the URL is reachable. "
    "ALWAYS perform one of the two actions: "
    "1. If the URL is not reachable, handoff to the summarizer. \n"
    "2. If the URL is reachable, handoff to the page inspector. "
)


def get_url_checker_agent():
    return Agent[JobScreenContext](
        name="UrlChecker",
        instructions=INSTRUCTIONS,
        tools=[check_url_reachability],
        model_settings=ModelSettings(tool_choice='required'),
        output_type=UrlVetterOutput,
        model="gpt-4o-mini",
    ) 
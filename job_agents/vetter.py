from agents import Agent, function_tool
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
            timeout=5,
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
    "You are a URL vetter. Your job is to check if a URL is reachable. "
    "If the URL is not reachable, record the status code and error message, "
    "then immediately summarize the result. If the URL is reachable, "
    "proceed to exract the job description from the URL. "
)


def get_url_vetter_agent():
    return Agent[JobScreenContext](
        name="UrlVetter",
        instructions=INSTRUCTIONS,
        tools=[check_url_reachability],
        output_type=UrlVetterOutput,
    ) 
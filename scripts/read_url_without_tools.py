"""
This tutorial script demonstrates how the Agent cannot reliably read a job posting from a URL (it makes stuff up)
"""
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio

load_dotenv()


class JobDescription(BaseModel):
    company: str
    title: str
    description: str
    requirements: list[str]
    responsibilities: list[str]
    qualifications: list[str]
    tools: list[str]


async def main(url: str):


    INSTRUCTIONS = (
        "Your job is to visit the URL and extract information about the job from the website. "
        "Do not include unrelated text such as equal opportunity statements or company descriptions. "
        "If the URL does not contain a job posting, or if you are unable to access the website, return a short error message explaining why. "
    )

    agent = Agent(
        name="ExtractJobDescriptionWithoutTools",
        instructions=INSTRUCTIONS,
        output_type=JobDescription,
        model="gpt-4.1",
    )

    results = await Runner.run(agent, input=url)
    print(results.final_output)

if __name__ == "__main__":
    test_url = "https://aurora.tech/careers/8014873002?gh_jid=8014873002"
    asyncio.run(main(test_url)) 
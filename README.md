# AI Job Search Agent w/ OpenAI Agents SDK + MCP

![Multi-agentic workflow](flowchart.png)

## Multi-Agent Job Discovery & Screening Orchestration

This repository contains a multi-agent system that automates job searching using the OpenAI Agents SDK. Specialized agents work together to handle tasks that a single agent cannot manage on its own.

Key features:

* **Multi-Agent Architecture**: Agents are connected with OpenAI Agent SDK handoffs, allowing models to intelligently decide which chain to follow. This also means we can fully leverage OpenAI's workflow tracing to examine handoff decisions.
* **MCP Tool Integration**: Connects to multiple Model Context Protocol (MCP) servers: SearxNG for web search and Playwright for JavaScript rendering and scraping.
* **Local Context Optimization**: Stores intermediate output and user preferences in local context instead of query history to achieve token cost optimization.
* **Parallel Execution**: Screen many job URLs at the same time, with each URL processed by its own agent pipeline.
  
The workflow is split into two pipelines:

1. **Job Searcher**: Gathers a list of job URLs.
2. **Job Screener**: Receives those URLs and processes them in parallel. For each URL, it generates a fit score and explanation based on the user’s resume and preferences.

## Example

Run the full search + screen pipeline and save results, restricting to first 10 results:

```bash
python main.py --job-title "software engineer" --resume example/resume.txt.sample --preferences example/preferences.txt.sample --output example/report.txt.sample --top-n 10
```
- Check out the output in the `example/` folder

Manually screen on user-provided URLs:

```bash
python main.py --job-title "software engineer" --resume example/resume.txt.sample --preferences example/preferences.txt.sample --output example/report.txt.sample --urls https://company.com/careers/ai-engineer-ii https://greenhouse.io/jobs/ml-scientist
```

Search only mode, just return URLs without screening

```bash
python main.py --job-title "software engineer" --search-only --output example/report.txt.sample 
```

## Agent Descriptions

### Job Searcher

- Utilizes the `web_search` tool provided by the **mcp-searxng** MCP server to discover job posting URLs.
- For now, issues queries in the format `"<job title> gh_jid"` with `pageno=1` and `language='en'`.
- Outputs a list of job URLs wrapped in the `SearchResults` model.

### Job Screener Multi-Agent

Processes each job URL through a sequence of agents linked by handoffs with built-in failsafes:

1. **UrlChecker** (`check_url_reachability` tool)
   - Checks URL reachability via HTTP GET and catches `403`, `404`, and other network errors.
   - If unreachable, records the error and jumps directly to the summary step.

2. **PageInspector** (`browser_navigate` tool)
   - Renders pages (including JavaScript) to verify if the content is a single job description.
   - If not a standalone job page (e.g., redirected to a company career board), logs the inspection reason and skips to summary.

3. **ExtractJobDescription** (`browser_wait_for` tool)
   - Waits up to 10 seconds for dynamic content to load.
   - Extracts company name, job title, and full job description (requirements, responsibilities, qualifications, tools).
   - Filters out unrelated sections such as equal opportunity statements.

4. **JobScreen** (`fetch_job_and_user_info` tool)
   - Evaluates fit between the extracted job description, the user's resume, and their preferences.
   - Assigns a fit score (1–5) with an accompanying rationale.

5. **SummaryAgent** (`fetch_job_screen_result` tool)
   - Consolidates the screening results into `SummaryAgentOutput`.
   - Gracefully logs any failures with the `failed` and `error_message` fields.

The logic above robustly handles network errors, proper loading of javascript content, non-job pages, and error logging for transparent reporting.

**Context Threading and Handoff Transition Between Agents:**

- **Context Threading**: Each agent pipeline maintains a shared `JobScreenContext` that gets populated and passed through the handoff chain, enabling sophisticated state management across agent boundaries.
- **Typed Handoff System**: Uses strongly-typed Pydantic models (`UrlResult`, `JobDescription`, `FitScore`) to ensure data integrity across agent transitions.

## MCP Servers

### mcp-searxng (Web Search)

We use SearXNG as a lean search tool alternative which avoids limits typical of other search engines, e.g.
- Google Custom Search Engine limits number of results to 100 per query
- Tavily limits the result to 20 per query

The downside to using SearXNG MCP is that we have to keep an docker container running locally as an http endpoint for the search.

To install and configure this server locally:

0. Install [mcp-searxng](https://github.com/ihor-sokoliuk/mcp-searxng)
   ```bash
   npm install -g mcp-searxng
   ```
   
1. Start the SearxNG MCP server:
   ```bash
   docker run -d --name searxng -p 8080:8080 searxng/searxng:latest
   ```
2. Enable JSON output:
   ```bash
   CONTAINER_ID=$(docker ps -qf "name=searxng")
   docker exec -it $CONTAINER_ID /bin/bash
   # In /etc/searxng/settings.yml, under search.formats, add "json"
   vi /etc/searxng/settings.yml
   docker restart searxng
   ```
3. Verify JSON response:
   ```bash
   curl -i "http://localhost:8080/search?q=hello&format=json"
   ```

### Playwright MCP Server (Scrape Dynamic Content)

Used by the **PageInspector** and **ExtractJobDescription** agents to render JavaScript-driven pages:

0. Install 
   ```bash
   npm i -g @playwright/mcp@latest
   ```
1. Ensure a `config.json` file is present (configures headless Chromium).
2. Start the [Playwright MCP server](https://github.com/microsoft/playwright-mcp/tree/675b083db372c148128d818927a2dbf84629ffd3):
   ```bash
   npx @playwright/mcp@latest --config config.json
   ```
3. Available tools: `browser_navigate`, `browser_wait_for`.

## Installation

### Prerequisites

- Node.js (`node -v` should show >= 20.0.0)
- Python 3.11+
- Docker

### Setup

```bash
git clone https://github.com/halstonblim/ai-job-search.git
cd job-search-agent-openai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure your environment in a `.env` file:
```ini
OPENAI_API_KEY=your_openai_api_key
```

Ensure both the SearxNG MCP and Playwright MCP servers are running before executing the pipeline. You can run the tutorial test scripts to make sure everything is working properly:
```bash
python scripts/playwright_mcp_tutorial.py
```

and 

```bash
python searxng_mcp_tutorial.py
```


## Project Structure

```text
.
├── main.py                       # Entrypoint to run the job search & screening flow
├── manager.py                    # Orchestrates the multi-agent workflow
├── config.json                   # Playwright MCP configuration
├── job_agents/                   # Agent definitions & shared tools
│   ├── searcher.py               # Builds the Job Searcher agent
│   ├── checker.py                # UrlChecker agent & reachability tool
│   ├── inspector.py              # PageInspector agent
│   ├── extractor.py              # ExtractJobDescription agent
│   ├── screener.py               # JobScreen agent
│   ├── summarizer.py             # SummaryAgent for results
│   └── context.py                # Shared Pydantic models & context management
├── scripts/                      # Tutorial and demo scripts
│   ├── searxng_mcp_tutorial.py       # Setup & use mcp-searxng web search
│   ├── playwright_mcp_tutorial.py    # Setup & use Playwright MCP server
│   └── screening_pipeline_demo.py    # Demo of the screening pipeline
├── example/                      # Sample input/output files
│   ├── resume.txt.sample
│   ├── preferences.txt.sample
│   └── result.txt.sample
├── requirements.txt              # Python dependencies
├── package.json                  # JS dependencies for Playwright MCP
└── README.md                     # This file
```

## Next Steps

- Increase number of search results
- Optimize token usage and costs for large-scale searches.
- Deploy with monitoring and autoscaling on cloud platforms.

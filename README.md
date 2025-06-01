# Job Search Agent

## Summary

This repository implements a multi-agent job search and screening pipeline using OpenAI models and an MCP-enabled web search (via SearxNG). The entrypoint is `main.py`, which:

1. Starts an MCP server to proxy web searches (command: `mcp-searxng`, configurable via `SEARXNG_URL` and `SEARXNG_MCP_TIMEOUT`).
2. Runs a **Job Search Agent** that issues web search queries and returns a list of job URLs.
3. For each URL, spins up a screening multi-agent workflow:
   - **UrlVetter**: checks reachability (tool: `check_url_reachability`).
   - **ExtractJobDescription**: fetches and summarizes the job posting (MCP tool). 
   - **JobScreen**: compares the description against your resume and preferences (tool: `fetch_job_and_user_info`) and assigns a fit score.
   - **SummaryAgent**: consolidates results (tool: `fetch_job_screen_result`).
4. Outputs a ranked report or a simple URL list when run in search-only mode.

Agent handoffs use typed filters and record functions to thread context through each stage, handling errors and tool outputs gracefully based on flexible agentic logic instead of hardcoded rules.

## Installation

### Prerequisites

- Node.js (v16+)
- Python 3.10+
- Docker

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/halstonblim/ai-job-search.git && cd job-search-agent-openai
   ```
2. Create and activate a Python virtual environment, then install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your OpenAI key and search server settings:
   ```ini
   OPENAI_API_KEY=your_openai_api_key
   SEARXNG_URL=http://localhost:8080
   SEARXNG_MCP_TIMEOUT=30
   ```
4. Launch the MCP-enabled web search server:
   ```bash
   docker run --rm -d -p 8080:8080 searxng/searxng:latest mcp-searxng
   ```

## Example

Run the full pipeline and write results to `result.txt.sample`:

```bash
python main.py \
  --job_title "remote software engineer job" \
  --resume resume.txt.sample \
  --preferences preferences.txt.sample \
  --top-n 10 \
  --output result.txt.sample
```

- `resume.txt.sample` — sample resume file
- `preferences.txt.sample` — sample preferences file
- `result.txt.sample` — sample output TSV/summary

## Project Structure

```text
.
├── main.py                   # Entrypoint to run the job search & screening flow
├── manager.py                # Orchestrates the multi-agent workflow
├── job_agents/               # Agent definitions & shared tools
│   ├── searcher.py           # Agent for job discovery
│   ├── vetter.py             # URL vetting agent + reachability tools
│   ├── extractor.py          # Job description extraction agent
│   ├── screener.py           # Resume/preferences screening agent
│   ├── summarizer.py         # Summarization agent for results
│   └── context.py            # Shared Pydantic models & utility functions
├── example/                  # Sample input/output files for testing/demo
│   ├── resume.txt.sample     # Example resume
│   ├── preferences.txt.sample# Example preferences
│   └── result.txt.sample     # Example output after screening
├── requirements.txt          # Project dependencies 
```

## Next Steps

- Handle dynamic JavaScript pages via a Playwright MCP plugin
- Implement deeper agentic crawling of company websites for targeted postings
- Add pagination support for retrieving many more search results and optimize OpenAI token usage across large URL sets
- Deploy the pipeline remotely (e.g., AWS/GCP/Azure) with monitoring and autoscaling

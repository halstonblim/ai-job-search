# Job Search Agent System

An evolving multi-agent system for automated job searching and screening, built with OpenAI Agents SDK and MCP (Model Control Protocol). The system combines job search capabilities with intelligent screening based on your resume.

**Current Status**: This project includes both a working single-URL job screening pipeline and tutorial components for learning the system. The full multi-agent orchestration is in development.

## Quick Start

### Configuration

1. Copy the example `.env.example` to `.env` and fill in your API keys:

```ini
OPENAI_API_KEY=
GOOGLE_API_KEY=
GOOGLE_CSE_ID=
```

2. Copy your resume into a plain text file called `resume.txt`

```
Experience
- Lots of good experience with python
- Lots of good experience with ML
Skill
- Skill A, Skill B
```

3. Modify the system prompt to include your job search preferences

## Architecture

This project follows a modular agent architecture with specialized components for different aspects of job search and screening:

```
├── job_agents/                  # Core agent modules
│   ├── __init__.py             # Package initialization  
│   ├── config.py               # Agent configuration and bundle creation
│   ├── context.py              # Shared context and error handling
│   ├── vetter.py               # URL validation agent
│   ├── extractor.py            # Job description extraction agent
│   ├── screener.py             # Job screening and fit analysis agent
│   └── summarizer.py           # Results summarization agent
├── scripts/                     # Demonstration scripts
│   └── job_screen_demo.py      # Complete job screening pipeline demo
├── notebooks/                   # Tutorial and exploration scripts
│   ├── mcp_searxng.py          # Basic MCP SearxNG usage tutorial
│   ├── web_search.py           # Web search functionality tutorial
│   ├── web_url_read.py         # URL reading and analysis tutorial
│   └── job_ranking_pipeline.ipynb # Google Custom Search job ranking notebook
├── main.py                     # Main orchestration script
├── resume.txt                  # Your resume for job fit analysis
└── requirements.txt            # Python dependencies
```

## Features

- **Modular Agent Pipeline**: Specialized agents with clear handoff patterns
- **MCP Integration**: Uses SearxNG MCP server for web search capabilities  
- **URL Validation**: Ensures job posting URLs are valid before processing
- **Intelligent Extraction**: Extracts job descriptions from various job board formats
- **Resume-Based Scoring**: Analyzes job fit based on your resume content
- **Structured Output**: Returns comprehensive job screening reports
- **Tutorial Scripts**: Learn how to use individual components

## Core Components

### Job Screening Pipeline (`scripts/job_screen_demo.py`)

A complete demonstration of the job screening pipeline that processes a single job posting URL through multiple specialized agents:

1. **URL Vetter Agent**: Validates that the provided URL is actually a job posting
2. **Extractor Agent**: Extracts the job description content from the URL using MCP SearxNG
3. **Screener Agent**: Analyzes the job posting against your resume and provides a fit score
4. **Summary Agent**: Generates a comprehensive summary of the screening results

The script demonstrates the handoff pattern between agents and includes error handling for failed pipeline steps. It's configured with example URLs and can be easily modified to test different job postings.

### Tutorial Scripts (`notebooks/`)

The notebooks directory contains several tutorial scripts to help you understand and use the system components:

#### `mcp_searxng.py`
Basic tutorial demonstrating how to:
- Initialize and connect to an MCP SearxNG server
- List available tools from the MCP server
- Create a simple search agent that uses SearxNG tools
- Perform web searches for general content (e.g., Python programming news)

#### `web_search.py`
Advanced web search tutorial showing how to:
- Build structured search queries for job postings
- Use specific search parameters (page numbers, language settings)
- Extract and structure job titles and URLs from search results
- Return typed results using Pydantic models for data validation

#### `web_url_read.py` 
URL reading and analysis tutorial demonstrating:
- How to validate URL accessibility before processing
- Reading and analyzing individual job posting pages
- Rating job postings with fit scores (0-5 scale)
- Handling errors and unreachable URLs gracefully

#### `job_ranking_pipeline.ipynb`
Jupyter notebook exploring an alternative approach using Google Custom Search Engine:
- Query Google's Custom Search JSON API for job postings
- Extract and normalize job data (title, company, location, description)
- Process large numbers of results (up to Google's 100-result limit)
- Parse job IDs from greenhouse.io URLs and handle duplicate detection
- Designed for eventual integration into the main agent workflow

## Agents

### 1. URL Vetter Agent
- Validates that URLs point to actual job postings
- Prevents wasted processing on invalid or non-job URLs
- Returns structured validation results

### 2. Extractor Agent  
- Extracts job description content from validated URLs
- Uses MCP SearxNG server for web page reading
- Handles various job board formats and layouts
- Returns clean, structured job content

### 3. Screener Agent
- Analyzes job postings against your resume
- Provides detailed fit scores and reasoning
- Identifies matching skills and experience
- Highlights potential concerns or gaps

### 4. Summary Agent
- Consolidates results from the entire pipeline
- Provides actionable recommendations
- Formats results for easy review and decision-making

## Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. **Setup SearxNG Server**
Make sure you have a SearxNG server running at `http://localhost:8080/` or update the URL in the configuration.

4. **Add Your Resume**
Place your resume content in `resume.txt` for job fit analysis.

## Usage

### Run the Job Screening Demo
```bash
python scripts/job_screen_demo.py
```

### Try the Tutorial Scripts
```bash
# Basic MCP SearxNG usage
python notebooks/mcp_searxng.py

# Web search for job postings  
python notebooks/web_search.py

# URL reading and analysis
python notebooks/web_url_read.py
```

### Explore Job Ranking (Jupyter)
```bash
jupyter notebook notebooks/job_ranking_pipeline.ipynb
```

### Use Individual Components
```python
import asyncio
from job_agents.config import build_job_search_agents

async def main():
    # Build agent bundle
    bundle = build_job_search_agents()
    
    # Run manager agent
    from agents import Runner
    result = await Runner.run(
        bundle.manager, 
        "Find data scientist jobs and analyze fit"
    )
    print(result)

asyncio.run(main())
```

## Roadmap

**Current**: Working single-URL job screening pipeline with tutorial components

**Planned Features**:
- Full multi-agent workflow orchestration
- Persistence and job search history
- Real-time new job alert triggers
- Enhanced web crawling capabilities
- Notification systems
- ATS integration for richer job data

## MCP Compatibility

This system demonstrates that **MCP is fully compatible** with modular agent architectures. The SearxNG MCP server is seamlessly integrated into the agent-as-tool pattern, allowing:

- Shared MCP servers across multiple agents
- Clean separation of concerns between agents
- Centralized MCP server management in the configuration layer

## Extending the System

The modular design makes it easy to add new capabilities:

1. **New Agent Types**: Add new specialist agents in the `job_agents/` folder
2. **Additional Tools**: Integrate new MCP servers or function tools  
3. **Enhanced Screening**: Add more sophisticated job analysis logic
4. **Data Storage**: Add persistent storage for job search history

## Output Format

The system returns structured job search reports containing:
- Search query and parameters
- Total jobs found and analyzed  
- Top job matches with fit scores
- Detailed analysis and recommendations

## Comparison to Original Structure

### Before (Separate Scripts)
- `searxng_tool.py` - Standalone job search script
- `searxng_urlread.py` - Standalone job screening script
- No coordination between agents

### After (Modular Architecture)  
- Specialist agents in `job_agents/` folder
- Complete pipeline demonstration in `scripts/`
- Educational tutorials in `notebooks/`
- Structured handoff patterns between agents
- Shared MCP server infrastructure
- Comprehensive error handling
- Easy to extend and maintain

## Resolving Naming Conflicts

**Important Note**: We renamed the local agents folder to `job_agents/` to avoid naming conflicts with the `openai-agents` package (which imports as `agents`). This ensures:

- Clean imports from the OpenAI Agents SDK: `from agents import Agent, Runner`
- No conflicts with our local modules: `from job_agents.config import build_job_search_agents`
- Better code organization and maintainability

## Dependencies

- `openai-agents`: OpenAI Agents SDK
- `python-dotenv`: Environment variable management
- `pydantic`: Data validation and serialization
- `mcp-searxng`: SearxNG MCP server (separate installation)
- `requests`: HTTP requests for URL validation
- `aiohttp`: Async HTTP client (for notebooks)
- `backoff`: Retry logic (for notebooks)

## License

MIT License

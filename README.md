# Job Search Agent

For now, this is a initial locally built search automation tool that scrapes job postings via Google Custom Search, enriches them through ATS APIs, and analyzes the job fit using an LLM-powered notebook. 
- This README will help you get started with the core scraper pipeline and outline the project's roadmap.

Eventually, this workflow will integrated into an Agent workflow, and we will be adding features like persistence, notifications, deeper web crawling, and real-time new job alert triggers

---

### Configuration

1. Copy the example `.env.example` to `.env` and fill in your API keys:

```ini
OPENAI_API_KEY=
GOOGLE_API_KEY=
GOOGLE_CSE_ID=
```

2. Copy your resume into a plain text filed called `resume.txt`

```
Experience
- Lots of good experience with python
- Lots of good experience with ML
Skill
- Skill A, Skill B
```

3. Modify the system prompt to include your job search preferences

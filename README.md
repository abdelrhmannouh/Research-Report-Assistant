# Research Report Assistant

A small multi-step LLM pipeline that takes a topic, researches it on the web, and
turns the findings into a polished written report.

Given a query, it runs three stages:

1. **Research** — a LangChain tool-calling agent (Groq `openai/gpt-oss-120b`) searches
   the web via the [Tavily](https://tavily.com) API and gathers raw notes.
2. **Analyze** — the raw notes are distilled into structured, factual bullet points
   grouped under section headings.
3. **Write** — the bullet points are turned into a short, well-organized report with
   an introduction, body, and conclusion.

## Project layout

```
main.py                  CLI entry point — prompts for a topic and prints the report
src/
  agents/agents.py        Research agent definition (LLM + web_search tool)
  pipeline/pipeline.py    Orchestrates research -> analyze -> write
  tools/tools.py          web_search tool, backed by Tavily
```

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your API keys:

   ```
   GROQ_API_KEY=your-groq-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```

## Usage

Run the CLI and enter a topic when prompted:

```bash
python main.py
```

The final report is printed to the console.

## Notes

- The research agent retries automatically (up to 3 attempts) on transient
  `tool_use_failed` errors from Groq.
- `web_search` returns the top 3 Tavily results (title, snippet, URL) for each query.

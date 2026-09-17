# Research Report Assistant

A small multi-step LLM pipeline that takes a topic, researches it on the web, and
turns the findings into a polished written report — available both as a CLI and
as a Streamlit web app.

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
app.py                    Streamlit web app (form, live status, downloadable report)
.streamlit/config.toml    Theme used by the Streamlit app
src/
  agents/agents.py        Research agent definition (LLM + web_search tool)
  pipeline/pipeline.py    Orchestrates research -> analyze -> write
  tools/tools.py          web_search tool, backed by Tavily
```

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv langAgent
   langAgent\Scripts\activate     # on Windows
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your API keys:

   ```
   GROQ_API_KEY=your-groq-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```

## Usage

### CLI

```bash
python main.py
```

Enter a topic when prompted; the final report is printed to the console.

### Web app

```bash
streamlit run app.py
```

Opens a browser UI where you can enter a topic, watch the research/analyze/write
steps run, read the generated report, and download it as Markdown.

> **Note on deployment:** this app is a Streamlit app, not a static site or
> serverless function, so it needs a host that keeps a persistent server process
> running (e.g. [Streamlit Community Cloud](https://streamlit.io/cloud), Render,
> Railway, or Hugging Face Spaces). Vercel's serverless model isn't a good fit for
> Streamlit's long-lived WebSocket connection.

## Notes

- The research agent retries automatically (up to 3 attempts) on transient
  `tool_use_failed` errors from Groq.
- `web_search` returns the top 3 Tavily results (title, snippet, URL) for each query.

## License

Licensed under the Apache License 2.0 — see [LICENSE](LICENSE).

© Abdelrhman Nouh. All rights reserved.

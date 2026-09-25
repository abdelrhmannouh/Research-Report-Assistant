# Research Report Assistant

A multi-step LLM pipeline that takes a topic, researches it on the web, and turns
the findings into a polished report with **inline citations and a Sources list**.
You can use it from a CLI, a Streamlit web app, or a FastAPI backend with live
progress streaming.

Given a topic, it runs three stages:

1. **Research**: a LangChain tool-calling agent (Groq `openai/gpt-oss-120b`) searches
   the web via [Tavily](https://tavily.com). Every result gets a stable number, `[n]`.
2. **Analyze**: the raw notes are distilled into structured, factual bullet points.
   The `[n]` citations are kept.
3. **Write**: the points become a short report (introduction, body, conclusion)
   with inline citations. A numbered **Sources** section is added at the end.

Each stage emits progress events (started or completed, elapsed time, number of
sources), so the UI and CLI show real progress while the report is generated.

## Architecture

```
   CLI (main.py)        Streamlit (app.py)
          \                  /
           \                /
            ReportClient (src/client.py)
            /                         \
   API_URL unset                  API_URL set
   (in-process)                   (HTTP + server-sent events)
          |                               |
          |                FastAPI (src/api/main.py)
          |                   POST /reports/stream
           \                 /
            ReportPipeline (src/pipeline/pipeline.py)
            research -> analyze -> write, yields StageEvents then a ReportResult
              |            |
   research agent      prompts (src/pipeline/prompts.py)
   + web_search tool
   (src/agents, src/tools)
```

```
main.py                  CLI: topic argument, --out file, progress on stderr
app.py                   Streamlit UI: live stage progress, report, sources, download
src/
  config.py              Settings from .env (pydantic-settings); clear missing-key errors
  llm.py                 Cached Groq chat model factory
  models.py              Source, StageEvent, ReportResult
  client.py              ReportClient: in-process or over HTTP/SSE
  tools/search.py        web_search tool + SourceCollector (dedupes and numbers sources)
  agents/research.py     Research agent definition
  pipeline/prompts.py    Analyst and writer prompt templates
  pipeline/pipeline.py   ReportPipeline orchestration, retries with backoff
  api/main.py            FastAPI app
tests/                   pytest suite (no network or API keys needed)
```

API clients are only created when a pipeline is built, not on import. A
missing key gives a clear message such as `GROQ_API_KEY is missing — add it to
your .env file.` instead of a stack trace.

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv langAgent
   langAgent\Scripts\activate     # on Windows
   pip install -r requirements-dev.txt
   ```

2. Copy `.env.example` to `.env` and fill in your keys:

   ```
   GROQ_API_KEY=your-groq-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```

   Optional settings: `MODEL`, `MAX_SEARCH_RESULTS`, `MAX_ATTEMPTS`, `API_URL`,
   and the `LANGSMITH_*` variables for tracing.

## Usage

### CLI

```bash
python main.py "solid state batteries"            # prints the report
python main.py "solid state batteries" -o out.md  # also saves it
python main.py                                    # prompts for a topic
```

### Web app

```bash
streamlit run app.py
```

By default the app runs the pipeline in-process. This is also how to deploy it
on Streamlit Community Cloud. To use the API backend instead, set
`API_URL=http://localhost:8000` in `.env`. The sidebar shows which backend is
active.

### API

```bash
uvicorn src.api.main:app --port 8000
```

| Method | Path              | Description                                              |
|--------|-------------------|----------------------------------------------------------|
| GET    | `/health`         | Liveness check                                           |
| POST   | `/reports`        | `{"topic": "..."}` → full `ReportResult` JSON             |
| POST   | `/reports/stream` | Server-sent events: `stage` events, then `result` or `error` |

The topic must be 3–300 characters. The API returns 422 for an invalid topic,
503 when API keys are missing, and 502 when generation fails. Interactive docs
are at `/docs`.

```bash
curl -N -X POST localhost:8000/reports/stream \
  -H "content-type: application/json" -d '{"topic": "quantum error correction"}'
```

## Tests

```bash
python -m pytest -q
```

The tests use a fake LLM and a fake researcher, so they run offline without API
keys. They cover source numbering, the pipeline's event order, retries,
Markdown and filename output, and the API endpoints, including SSE framing.

## Notes

- The research step retries up to `MAX_ATTEMPTS` times, with increasing backoff,
  when Groq returns a transient `tool_use_failed` error.
  Sources from failed attempts are discarded.
- Streamlit and FastAPI both need a host that keeps a server process running,
  such as Streamlit Community Cloud, Render, Railway, or Hugging Face Spaces.
  Vercel's serverless model isn't a good fit.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).

© Abdelrhman Nouh. All rights reserved.

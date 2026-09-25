import time
from collections.abc import Callable, Iterator

from groq import BadRequestError
from langchain_core.language_models import BaseChatModel

from src.agents.research import build_research_agent
from src.config import Settings, get_settings
from src.llm import get_llm
from src.models import ReportResult, StageEvent
from src.pipeline.prompts import ANALYST_PROMPT, WRITER_PROMPT
from src.tools.search import SourceCollector, make_tavily_search, make_web_search_tool

# Runs the research step: given a topic, searches the web (recording every
# result in the collector) and returns raw notes.
Researcher = Callable[[str, SourceCollector], str]


def make_agent_researcher(llm: BaseChatModel, settings: Settings) -> Researcher:
    search = make_tavily_search(settings.tavily_api_key, settings.max_search_results)

    def research(topic: str, collector: SourceCollector) -> str:
        # The tool is bound to this run's collector, so concurrent runs
        # (e.g. parallel API requests) never share sources.
        agent = build_research_agent(llm, make_web_search_tool(collector, search))
        response = agent.invoke(
            {"messages": [{"role": "user", "content": topic}]},
            {"recursion_limit": settings.recursion_limit},
        )
        return response["messages"][-1].content

    return research


class ReportPipeline:
    """Research -> analyze -> write, reporting progress as it goes."""

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        researcher: Researcher | None = None,
        settings: Settings | None = None,
        retry_on: tuple[type[Exception], ...] = (BadRequestError,),
    ) -> None:
        self.settings = settings or get_settings()
        if llm is None or researcher is None:
            self.settings.require_keys()
        self.llm = llm or get_llm()
        self.researcher = researcher or make_agent_researcher(self.llm, self.settings)
        self.retry_on = retry_on

    def _research(self, topic: str) -> tuple[str, SourceCollector]:
        # The model occasionally emits malformed JSON for tool call arguments
        # on Groq, which raises BadRequestError ("tool_use_failed"). That's
        # generation flakiness, not a real invalid request, so retry it.
        for attempt in range(1, self.settings.max_attempts + 1):
            collector = SourceCollector()
            try:
                return self.researcher(topic, collector), collector
            except self.retry_on:
                if attempt == self.settings.max_attempts:
                    raise
                time.sleep(self.settings.retry_backoff_seconds * attempt)
        raise AssertionError("unreachable")

    def run_stream(self, topic: str) -> Iterator[StageEvent | ReportResult]:
        timings: dict[str, float] = {}

        def timed(stage, fn):
            start = time.perf_counter()
            value = fn()
            timings[stage] = round(time.perf_counter() - start, 2)
            return value

        yield StageEvent(stage="research", status="started")
        notes, collector = timed("research", lambda: self._research(topic))
        sources = collector.sources
        yield StageEvent(
            stage="research", status="completed", elapsed=timings["research"],
            detail=f"{len(sources)} source{'s' if len(sources) != 1 else ''}",
        )

        yield StageEvent(stage="analyze", status="started")
        points = timed("analyze", lambda: (ANALYST_PROMPT | self.llm).invoke(
            {"topic": topic, "notes": notes}).content)
        yield StageEvent(stage="analyze", status="completed", elapsed=timings["analyze"])

        yield StageEvent(stage="write", status="started")
        report = timed("write", lambda: (WRITER_PROMPT | self.llm).invoke(
            {"topic": topic, "points": points}).content)
        yield StageEvent(stage="write", status="completed", elapsed=timings["write"])

        yield ReportResult(topic=topic, report=report, sources=sources, timings=timings)

    def run(self, topic: str) -> ReportResult:
        for item in self.run_stream(topic):
            if isinstance(item, ReportResult):
                return item
        raise AssertionError("pipeline finished without a result")


def pipeline(query: str) -> str:
    """Backwards-compatible helper: returns the report with its Sources section."""
    return ReportPipeline().run(query).to_markdown()
